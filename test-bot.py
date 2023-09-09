import os
import random
import fitz
from telegram import Update
from telegram.ext import Updater, MessageHandler, Filters, CommandHandler, CallbackContext
import gspread
from google.oauth2.service_account import Credentials
import spacy  # For NER
from transformers import pipeline  # For text classification (using Hugging Face Transformers)

# Replace 'YOUR_BOT_TOKEN' with the API token you received from BotFather
BOT_TOKEN = 'YOUR_BOT_TOKEN'

# Replace 'YOUR_GOOGLE_SHEETS_CREDENTIALS' with the JSON file containing your Google Sheets credentials
GOOGLE_SHEETS_CREDENTIALS = 'YOUR_GOOGLE_SHEETS_CREDENTIALS'

# Replace 'YOUR_SHEET_ID' with the ID of your sheet in Google Sheets
SHEET_ID = 'YOUR_SHEET_ID'


# Add a list of multiple-choice options
MULTIPLE_CHOICE_OPTIONS = ["Option A", "Option B", "Option C", "Option D"]

def start(update: Update, context: CallbackContext):
    update.message.reply_text("Send me a PDF file, and I'll extract text from it.")

def extract_cases_from_text(all_text):
    cases = []
    current_case = ""

    for line in all_text.split('\n'):
        if line.startswith("Case:"):
            # A new case begins
            if current_case:
                cases.append(current_case)
            current_case = line
        else:
            current_case += "\n" + line

    # Append the last case
    if current_case:
        cases.append(current_case)

    return cases

def generate_question_from_case(case):
    # You can implement your logic to generate questions from the case here
    # For example, you can split the case into sentences and randomly select one as a question
    sentences = case.split('.')
    if sentences:
        question = random.choice(sentences).strip() + '?'
        options = random.sample(MULTIPLE_CHOICE_OPTIONS, 4)  # Randomly select 4 options
        options.append(question)  # Add the correct answer as one of the options
        random.shuffle(options)  # Shuffle the options
        return {
            'question': question,
            'options': options
        }
    else:
        return "No question generated for this case."

def handle_pdf(update: Update, context: CallbackContext):
    file = update.message.document.get_file()
    file.download('input.pdf')
    
    pdf_document = fitz.open('input.pdf')
    all_text = ''
    
    for page_number in range(len(pdf_document)):
        page = pdf_document[page_number]
        all_text += page.get_text()
    
    # Split the extracted text into cases based on subjects or titles
    cases = extract_cases_from_text(all_text)
    
    # Authenticate with Google Sheets using your credentials
    credentials = Credentials.from_service_account_file(GOOGLE_SHEETS_CREDENTIALS, scopes=['https://www.googleapis.com/auth/spreadsheets'])
    gc = gspread.authorize(credentials)
    
    # Open the Google Sheet
    sheet = gc.open_by_key(SHEET_ID).sheet1
    
    # Upload each case to the Google Sheet
    for case in cases:
        sheet.append_row([case.strip()])  # Assuming you want one case per row
    
    # Generate questions from the cases
    generated_questions = [generate_question_from_case(case) for case in cases]
    
    # Send the generated questions back to the user
    for question in generated_questions:
        update.message.reply_text(question)

def generate_question_from_sheet(user_input, sheet_data):
    # Implement logic to generate questions from the Google Sheet data based on user input
    # For example, search for relevant information in the sheet and construct questions
    questions = []

    # Here's a simple example: search for cases containing user input keywords
    for row in sheet_data:
        if any(keyword.lower() in row.lower() for keyword in user_input.split()):
            questions.append(generate_question_from_case(row))
    
    return questions

def handle_text_input(update: Update, context: CallbackContext):
    user_input = update.message.text
    
    # Authenticate with Google Sheets using your credentials
    credentials = Credentials.from_service_account_file(GOOGLE_SHEETS_CREDENTIALS, scopes=['https://www.googleapis.com/auth/spreadsheets'])
    gc = gspread.authorize(credentials)
    
    # Open the Google Sheet
    sheet = gc.open_by_key(SHEET_ID).sheet1
    
    # Fetch data from the Google Sheet (assuming it's a single column of data)
    sheet_data = sheet.col_values(1)
    
    # Generate questions based on user input and sheet data
    generated_questions = generate_question_from_sheet(user_input, sheet_data)
    
    if generated_questions:
        for question in generated_questions:
            update.message.reply_text(question)
    else:
        update.message.reply_text("No questions found based on your input.")

def main():
    updater = Updater(BOT_TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.document.mime_type("application/pdf"), handle_pdf))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_text_input))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
