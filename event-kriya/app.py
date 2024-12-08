from flask import Flask, render_template, request, redirect, url_for, flash, session, make_response,jsonify,send_from_directory
from pymongo import MongoClient
from reportlab.pdfgen import canvas  # Using ReportLab for PDF generation
from reportlab.lib.pagesizes import letter
import os  # For managing file paths
from PyPDF2 import PdfReader, PdfWriter
from xhtml2pdf import pisa
import io
from io import BytesIO
import PyPDF2  
from datetime import datetime
import uuid
import shutil
from PyPDF2 import PdfMerger

app = Flask(__name__)
app.secret_key = 'xyz1234nbg789ty8inmcv2134'  # Make sure this key is kept secure

# MongoDB connection
MONGO_URI = "mongodb+srv://Entries:ewp2025@cluster0.1tuj7.mongodb.net/event-kriya?retryWrites=true&w=majority"
client = MongoClient(MONGO_URI)
db = client["event-kriya"]
event_collection = db["event-entries"]

# Main route for home
@app.route('/')
def home():
    # session.clear()  # Clear all session data for a new event
    return render_template('home.html')

@app.route('/event-instructions', methods=['GET', 'POST'])
def event_instructions():
    if request.method == 'POST':
        return redirect(url_for('event_detail'))
    return render_template('event_instruction.html')

# Event Details Form
@app.route('/event-detail', methods=['GET', 'POST'])
def event_detail():
    if request.method == 'POST':
        # Collect event details and store in session
        event_details = {
            'secretary_name': request.form['secretary_name'],
            'secretary_roll_number': request.form['secretary_roll_number'],
            'secretary_mobile': request.form['secretary_mobile'],
            'convenor_name': request.form['convenor_name'],
            'convenor_roll_number': request.form['convenor_roll_number'],
            'convenor_mobile': request.form['convenor_mobile'],
            'faculty_advisor_name': request.form['faculty_advisor_name'],
            'faculty_advisor_designation': request.form['faculty_advisor_designation'],
            'faculty_advisor_contact': request.form['faculty_advisor_contact'],
            'judge_name': request.form['judge_name'],
            'judge_designation': request.form['judge_designation'],
            'judge_contact': request.form['judge_contact']
        }
        session['event_details'] = event_details
        return redirect(url_for('event_page'))
    return render_template('event_detail.html')

# Event Data Form
@app.route('/event', methods=['GET', 'POST'])
def event_page():
    if request.method == 'POST':
        # Collect event data and store in session
        event_data = {
            'day_1': 'day_1' in request.form,
            'day_2': 'day_2' in request.form,
            'day_3': 'day_3' in request.form,
            'two_days': request.form.get('two_days'),
            'rounds': request.form.get('rounds'),
            'participants': request.form.get('participants'),
            'individual': 'individual' in request.form,
            'team': 'team' in request.form,
            'team_min': request.form.get('team_min'),
            'team_max': request.form.get('team_max'),
            'halls_required': request.form.get('halls_required'),
            'preferred_halls': request.form.get('preferred_halls'),
            'slot': request.form.get('slot'),
            'extension_boxes': request.form.get('extension_boxes'),
            'event_description': request.form.get('event_description'),
            'event_location': request.form.get('event_location')
        }
        session['event_data'] = event_data
        return redirect(url_for('items_page'))
    return render_template('event.html')


@app.route('/items', methods=['GET', 'POST'])
def items_page():
    if 'event_items' not in session:
        session['event_items'] = []

    if request.method == 'POST':
        # Collect item data from the form and store it in the session
        try:
            item_data = {
                "sno": request.form.get("sno"),
                "item_name": request.form.get("item_name"),
                "quantity": int(request.form.get("quantity")),
                "price_per_unit": float(request.form.get("price_per_unit")),
                "total_price": int(request.form.get("quantity")) * float(request.form.get("price_per_unit"))
            }

            # Validate required fields
            if not item_data["item_name"] or not item_data["quantity"]:
                flash("Item name and quantity are required.")
                return redirect(url_for('items_page'))

            # Append item to session
            session['event_items'].append(item_data)
            flash("Item added successfully!")
            return redirect(url_for('event_summary'))
        except ValueError:
            flash("Please enter valid numeric values for quantity and price.")
            return redirect(url_for('items_page'))

    return render_template('items.html', event_items=session['event_items'])

# Event Summary Form
@app.route('/event-summary', methods=['GET', 'POST'])
def event_summary():
    if request.method == 'POST':
        event_name = request.form.get('name')
        tagline = request.form.get('tagline')
        about = request.form.get('about')
        rounds = []

        round_count = int(request.form.get('round_count', 0))
        for i in range(round_count):
            rounds.append({
                "round_no": i + 1,
                "name": request.form.get(f'round_name_{i}'),
                "description": request.form.get(f'round_description_{i}'),
                "rules": request.form.get(f'round_rules_{i}')
            })

        session['event_summary'] = {
            "name": event_name,
            "tagline": tagline,
            "about": about,
            "rounds": rounds
        }
        return redirect(url_for('preview'))
    return render_template('event_form.html')


@app.route('/preview', methods=['GET'])
def preview():
    try:
        # Retrieve event details, event data, event items, and event form data from session
        event_details = session.get('event_details', {})
        event_data = session.get('event_data', {})
        event_items = session.get('event_items', [])
        event_form_data = session.get('event_form_data', {})

        # Pass all the data to the template
        return render_template('preview.html', 
                               event_details=event_details, 
                               event_data=event_data,
                               event_items=event_items,
                               event_form_data=event_form_data)
    except Exception:
        return jsonify({"status": "error", "message": "Error retrieving preview data"}), 500
@app.route('/submit_event', methods=['POST'])
def submit_event():
    try:
        # Get the request JSON data
        all_event_data = request.get_json()  # Correct method to get JSON data
        event_details = all_event_data.get('eventDetails')
        event_data = all_event_data.get('eventData')
        event_items = all_event_data.get('eventItems')  # Correct field name should match
        event_summary = all_event_data.get('eventFormData')

        # Log the received data to ensure it's correct
        print("Received event details:", event_details)
        print("Received event data:", event_data)
        print("Received event items:", event_items)  # Log items
        print("Received event summary:", event_summary)

        # Generate a new event ID based on the last event ID in the database
        existing_event = event_collection.find_one(sort=[("event_id", -1)])
        if existing_event and "event_id" in existing_event:
            last_event_num = int(existing_event["event_id"][4:])
            new_event_id = f"EVNT{last_event_num + 1:02d}"
        else:
            new_event_id = "EVNT01"

        # Prepare the event entry for the database
        event_entry = {
            "event_id": new_event_id,
            "details": event_details,
            "event": event_data,
            "items": event_items,
            "form": event_summary,
        }
        print("Event Entry to be inserted:", event_entry)
        
        # Insert data into the database
        event_collection.insert_one(event_entry)

        session["event_id"] = new_event_id

        return jsonify({"status": "success", "message": "Event submitted successfully!", "event_id": new_event_id}), 200

    except Exception as e:
        print("Error during event submission:", str(e))
        return jsonify({"status": "error", "message": str(e)}), 500


# Confirmation Page
@app.route('/confirm')
def confirm_page():
    event_id=session.get("event_id")
    return render_template('confirm.html',event_id=event_id)






@app.route('/view-preview', methods=['GET'])
def view_preview():
    # Retrieve event_id from session
    event_id = session.get("event_id")
    if not event_id:
        flash("No event ID found in session.")
        return redirect(url_for('event_page'))

    # Fetch event data from MongoDB
    event_datas = event_collection.find_one({"event_id": event_id})
    if not event_datas:
        flash("Event data not found.")
        return redirect(url_for('event_page'))

    try:
        # Fetch form data for rendering in event_preview.html
        form_data = event_datas.get("details", {})
        event_data = event_datas.get("form", {})
        items = event_datas.get("items", {})

        # Generate and save multiple pages as PDFs
        pdf_filenames = []
        pdf_filepaths = []

        # Page 1
        html_content_page_1 = render_template('event_start.html')
        pdf_output_page_1 = generate_pdf(html_content_page_1)
        pdf_filename_page_1 = generate_unique_filename("event_page1")
        pdf_filepath_page_1 = os.path.join('static', 'uploads', pdf_filename_page_1)
        save_pdf(pdf_output_page_1, pdf_filepath_page_1)
        pdf_filenames.append(pdf_filename_page_1)
        pdf_filepaths.append(pdf_filepath_page_1)

        # Page 2
        html_content_page_2 = render_template('page2.html')
        pdf_output_page_2 = generate_pdf(html_content_page_2)
        pdf_filename_page_2 = generate_unique_filename("event_page2")
        pdf_filepath_page_2 = os.path.join('static', 'uploads', pdf_filename_page_2)
        save_pdf(pdf_output_page_2, pdf_filepath_page_2)
        pdf_filenames.append(pdf_filename_page_2)
        pdf_filepaths.append(pdf_filepath_page_2)

        # Page 3 (Event preview page)
        html_content_page_3 = render_template(
            'event_preview.html',
            event_id=event_id,
            form_data=form_data,
            event_datas=event_datas
        )
        pdf_output_page_3 = generate_pdf(html_content_page_3)
        pdf_filename_page_3 = generate_unique_filename("event_page3")
        pdf_filepath_page_3 = os.path.join('static', 'uploads', pdf_filename_page_3)
        save_pdf(pdf_output_page_3, pdf_filepath_page_3)
        pdf_filenames.append(pdf_filename_page_3)
        pdf_filepaths.append(pdf_filepath_page_3)

        # Page 4 - Using PdfWriter (No template, programmatically generated)
        pdf_filename_page_4 = generate_unique_filename("event_page4")
        pdf_filepath_page_4 = os.path.join('static', 'uploads', pdf_filename_page_4)
        generate_and_save_pdf_page4(pdf_filepath_page_4, event_data)
        pdf_filenames.append(pdf_filename_page_4)
        pdf_filepaths.append(pdf_filepath_page_4)

        # Page 5 (Items Preview)
        html_content_page_5 = render_template(
            'items_preview.html',
            event_id=event_id,
            items=items,
            event_datas=event_datas
        )
        pdf_output_page_5 = generate_pdf(html_content_page_5)
        pdf_filename_page_5 = generate_unique_filename("event_page5")
        pdf_filepath_page_5 = os.path.join('static', 'uploads', pdf_filename_page_5)
        save_pdf(pdf_output_page_5, pdf_filepath_page_5)
        pdf_filenames.append(pdf_filename_page_5)
        pdf_filepaths.append(pdf_filepath_page_5)

        # Merge the PDFs
        merged_pdf_filename = f"{event_id}_combined.pdf"
        merged_pdf_filepath = os.path.join('static', 'uploads', merged_pdf_filename)

        # Use PdfMerger to combine PDFs
        merger = PdfMerger()

        for pdf_path in pdf_filepaths:
            merger.append(pdf_path)

        # Write the merged PDF to the server
        merger.write(merged_pdf_filepath)
        merger.close()

        # Provide the merged PDF for download
        flash(f"PDF successfully created and saved: {merged_pdf_filename}")

        # Clean up intermediate PDFs (delete them)
        for pdf_path in pdf_filepaths:
            os.remove(pdf_path)

        return send_from_directory(
            'static/uploads', 
            merged_pdf_filename, 
            as_attachment=True
        )

    except Exception as e:
        print(f"Error during preview: {e}")
        flash("An error occurred while generating the preview.")
        return redirect(url_for('event_page'))

def generate_unique_filename(prefix):
    """Generate a unique filename using a UUID and prefix."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4().hex[:6])  # Generates a short unique string
    return f"{prefix}_{timestamp}_{unique_id}.pdf"

def generate_pdf(html_content):
    """Generate PDF from HTML content using xhtml2pdf."""
    pdf_output = BytesIO()  # This creates an in-memory binary stream
    pisa_status = pisa.CreatePDF(html_content, dest=pdf_output)
    if pisa_status.err:
        raise Exception("Error occurred while generating the PDF.")
    pdf_output.seek(0)  # Rewind the buffer to the beginning
    return pdf_output.read()

def save_pdf(pdf_output, filepath):
    """Save the generated PDF to the specified filepath."""
    with open(filepath, "wb") as pdf_file:
        pdf_file.write(pdf_output)

def generate_and_save_pdf_page4(filepath, event_data):
    """Generate a custom PDF for page 4 using PdfWriter (programmatically created)."""
   

    # Create a BytesIO buffer to hold the generated PDF
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Set margin for text placement
    margin = 60  # Left margin
    content_width = width - 2 * margin
    content_height = height - 2 * margin

    # Draw a straightened horizontal line above the Day 1 contents
    pdf.line(margin - 20, height - 40, width - margin, height - 40)

    # Draw checkboxes for days (horizontally aligned)
    pdf.drawString(margin, height - 60, "Day 1:")
    pdf.rect(margin + 40, height - 61, 10, 10, fill=1 if "day1" in event_data.get("day", []) else 0)

    pdf.drawString(margin + 80, height - 60, "Day 2:")
    pdf.rect(margin + 130, height - 61, 10, 10, fill=1 if "day2" in event_data.get("day", []) else 0)

    pdf.drawString(margin + 170, height - 60, "Both Days:")
    pdf.rect(margin + 250, height - 61, 10, 10, fill=1 if "bothDays" in event_data.get("day", []) else 0)

    # Draw a line after the checkboxes
    pdf.line(margin - 20, height - 80, width - margin, height - 80)

    # Draw vertical lines from the top horizontal line to the bottom horizontal line
    pdf.line(margin - 20, height - 40, margin - 20, height - 480)  # Left vertical line
    pdf.line(width - margin, height - 40, width - margin, height - 480)  # Right vertical line

    # Draw text fields for event data
    pdf.drawString(margin, height - 110, f"Expected No. of Participants: {event_data.get('participants', '')}")
    pdf.drawString(margin, height - 140, f"Team Size: Min: {event_data.get('teamSizeMin', '')}, Max: {event_data.get('teamSizeMax', '')}")

    # Draw a line after participants and team size
    pdf.line(margin - 20, height - 150, width - margin, height - 150)

    pdf.drawString(margin, height - 170, f"Number of Halls/Labs Required: {event_data.get('hallsRequired', '')}")
    pdf.drawString(margin, height - 200, "Reason for Multiple Halls:")
    pdf.drawString(margin + 20, height - 220, event_data.get("hallReason", ""))

    # Draw a line after halls and reasons
    pdf.line(margin - 20, height - 230, width - margin, height - 230)

    pdf.drawString(margin, height - 250, "Halls/Labs Preferred:")
    pdf.drawString(margin + 20, height - 270, event_data.get("hallsPreferred", ""))

    # Draw a line after halls preferred
    pdf.line(margin - 20, height - 280, width - margin, height - 280)

    # Draw radio buttons for duration
    pdf.drawString(margin, height - 300, "Duration of the Event in Hours:")
    pdf.drawString(margin + 20, height - 320, "Slot 1: 9:30 to 12:30")
    pdf.circle(margin + 160, height - 315, 5, fill=1 if event_data.get("duration") == "slot1" else 0)
    pdf.drawString(margin + 20, height - 340, "Slot 2: 1:30 to 4:30")
    pdf.circle(margin + 160, height - 335, 5, fill=1 if event_data.get("duration") == "slot2" else 0)
    pdf.drawString(margin + 20, height - 360, "Full Day")
    pdf.circle(margin + 160, height - 355, 5, fill=1 if event_data.get("duration") == "fullDay" else 0)

    # Draw a line after the duration radio buttons
    pdf.line(margin - 20, height - 370, width - margin, height - 370)

    pdf.drawString(margin, height - 390, f"Number Required: {event_data.get('numberRequired', '')}")
    pdf.drawString(margin, height - 420, "Reason for Number:")
    pdf.drawString(margin + 20, height - 440, event_data.get("numberReason", ""))

    # Draw a line after number and reason
    pdf.line(margin - 20, height - 450, width - margin, height - 450)

    pdf.drawString(margin, height - 470, f"Extension Box: {event_data.get('extensionBox', '')}")

    # Draw a line after the extension box
    pdf.line(margin - 20, height - 480, width - margin, height - 480)

    # Draw signature fields
    pdf.drawString(margin-15, height - 550, f"Signature of the Secretary: ")
    pdf.drawString(margin-15, height - 580, f"Signature of the Faculty Advisor: ")

    # Save the generated PDF
    pdf.save()

    # Move buffer back to the beginning and return it
    buffer.seek(0)

    # Write the PDF to the specified filepath
    with open(filepath, "wb") as f:
        f.write(buffer.read())

if __name__ == '__main__':
    app.run(debug=True)

