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
workshop_collection=db["workshop-entries"]

# Main route for home
@app.route('/')
def home():
    # session.clear()  # Clear all session data for a new event
    return render_template('home.html')
@app.route('/event-info', methods=['GET', 'POST'])
def event_info():
    if request.method == 'POST':
        # Collect event details and store in session
        event_details = {
            'association_name': request.form['association_name'],
            'event_name': request.form['event_name']
        }
        session['event_info'] = event_details
        return redirect(url_for('event_instructions'))

    return render_template('event_info.html')

    

@app.route('/event_instructions', methods=['GET', 'POST'])
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
            'technical_event':'technical_event' in request.form,
            'non_technical_event':'non_technical_event' in request.form,
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
@app.route('/event_summary', methods=['GET', 'POST'])
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
        association_name=all_event_data.get('association_name')
        event_name=all_event_data.get('event_name')

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
            "association_name":association_name,
            "event_name":event_name
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
        association_name=event_datas.get("association_name")
        event_name=event_datas.get("event_name")

        form_data = event_datas.get("details", {})
        event_data = event_datas.get("form", {})
        items = event_datas.get("items", {})
        event_rounds=event_datas.get("event",{})

        # Generate and save multiple pages as PDFs
        pdf_filenames = []
        pdf_filepaths = []

        # Page 1
        html_content_page_1 = render_template(
            'event_start.html',
            event_id=event_id,
            association_name=association_name,
            event_name=event_name,
            event_datas=event_datas
        )
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

        html_content_page_6 = render_template(
            'rounds_preview.html',
            event_id=event_id,
            event_rounds=event_rounds,
            event_datas=event_datas
        )
        pdf_output_page_6 = generate_pdf(html_content_page_6)
        pdf_filename_page_6 = generate_unique_filename("event_page6")
        pdf_filepath_page_6 = os.path.join('static', 'uploads', pdf_filename_page_6)
        save_pdf(pdf_output_page_6, pdf_filepath_page_6)
        pdf_filenames.append(pdf_filename_page_6)
        pdf_filepaths.append(pdf_filepath_page_6)

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
        # flash(f"PDF successfully created and saved: {merged_pdf_filename}")

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
    """Generate a custom PDF for page 4 with aligned checkboxes and padding."""
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Margins and padding
    margin = 60
    padding = 20
    content_width = width - 2 * margin

    # Top horizontal line
    pdf.line(margin, height - 40, width - margin, height - 40)

    # Vertical lines
    vertical_line_x = margin + padding
    pdf.line(margin, height - 40, margin, height - 540)
    pdf.line(width - margin, height - 40, width - margin, height - 540)

    y_pos = height - 60

    # Draw circular checkboxes for days
    label_x = vertical_line_x + 5
    checkbox_x = label_x + 100

    # Ensure alignment and spacing of days
    pdf.drawString(label_x, y_pos-10, "Day 1:")
    pdf.circle(checkbox_x-55, y_pos-5 , 5, fill=1 if event_data.get("day_1") else 0)

    pdf.drawString(label_x + 120, y_pos-10, "Day 2:")
    pdf.circle(checkbox_x +65, y_pos-5 , 5, fill=1 if event_data.get("day_2") else 0)

    pdf.drawString(label_x + 240, y_pos-10, "Day 3:")
    pdf.circle(checkbox_x + 185, y_pos-6 , 5, fill=1 if event_data.get("day_3") else 0)

    pdf.drawString(label_x + 360, y_pos-10, "Two Days:")
    pdf.circle(checkbox_x + 328, y_pos-6, 5, fill=1 if event_data.get("two_days") else 0)

    # Horizontal line
    y_pos -= 30
    pdf.line(margin, y_pos, width - margin, y_pos)

    # Event type
    y_pos -= 20
    pdf.drawString(label_x, y_pos-10, "Technical Event:")
    pdf.circle(checkbox_x, y_pos - 6, 5, fill=1 if event_data.get("technical_event") else 0)

    pdf.drawString(label_x + 180, y_pos-10, "Non-Technical Event:")
    pdf.circle(checkbox_x + 205, y_pos - 6, 5, fill=1 if event_data.get("non_technical_event") else 0)

    # Horizontal line
    y_pos -= 30
    pdf.line(margin, y_pos, width - margin, y_pos)
    center_x = width / 2  # Calculate the center of the page
    top_y = y_pos+50   # Y-position of the top horizontal line
    bottom_y = y_pos   # Y-position of the bottom horizontal line
    pdf.line(center_x-80, top_y, center_x-80, bottom_y)
    # Rounds
    y_pos -= 20
    pdf.drawString(label_x, y_pos-10, f"Rounds: {event_data.get('rounds', 'N/A')}")

    # Horizontal line
    y_pos -= 30
    pdf.line(margin, y_pos, width - margin, y_pos)

    # Participants
    y_pos -= 20
    pdf.drawString(label_x, y_pos-10, f"Participants: {event_data.get('participants', 'N/A')}")

    # Horizontal line
    y_pos -= 30
    pdf.line(margin, y_pos, width - margin, y_pos)

    # Team information
    y_pos -= 20
    pdf.drawString(label_x+5, y_pos-7, "Individual:")
    pdf.circle(checkbox_x-30, y_pos-2, 5, fill=1 if event_data.get("individual") else 0)

    pdf.drawString(label_x + 235, y_pos, "Team:")
    pdf.circle(checkbox_x + 190, y_pos+3 , 5, fill=1 if event_data.get("team") else 0)

    y_pos -= 20
    pdf.drawString(label_x+235, y_pos, f"Min Size: {event_data.get('team_min', 'N/A')}")
    pdf.drawString(label_x + 235, y_pos-20, f"Max Size: {event_data.get('team_max', 'N/A')}")

    # Horizontal line
    y_pos -= 30
    pdf.line(margin, y_pos, width - margin, y_pos)
    center_x = width / 2  # Calculate the center of the page
    top_y = y_pos+70   # Y-position of the top horizontal line
    bottom_y = y_pos   # Y-position of the bottom horizontal line
    pdf.line(center_x, top_y, center_x, bottom_y)

    # Halls and slots
    y_pos -= 20
    pdf.drawString(label_x, y_pos-4, f"Halls Required: {event_data.get('halls_required', 'N/A')}")
    y_pos -= 20
    pdf.drawString(label_x, y_pos-4, f"Preferred Halls: {event_data.get('preferred_halls', 'N/A')}")

    # Horizontal line
    y_pos -= 30
    pdf.line(margin, y_pos, width - margin, y_pos)

    # Slots
    y_pos -= 20
    pdf.drawString(label_x, y_pos-5, "Slot Details:")
    y_pos -= 20
    pdf.drawString(label_x + 20, y_pos-5, "Slot 1: 9:30 to 12:30")
    pdf.circle(checkbox_x + 40, y_pos - 1, 5, fill=1 if event_data.get("slot1")  else 0)

    y_pos -= 20
    pdf.drawString(label_x + 20, y_pos-5, "Slot 2: 1:30 to 4:30")
    pdf.circle(checkbox_x + 40, y_pos - 1, 5, fill=1 if event_data.get("slot2")  else 0)

    y_pos -= 20
    pdf.drawString(label_x + 20, y_pos-5, "Full Day")
    pdf.circle(checkbox_x + 40, y_pos - 1, 5, fill=1 if event_data.get("full_day")  else 0)

    # Horizontal line
    y_pos -= 30
    pdf.line(margin, y_pos, width - margin, y_pos)

    # Extension boxes
    y_pos -= 20
    pdf.drawString(label_x, y_pos-5, f"Extension Boxes: {event_data.get('extension_boxes', 'N/A')}")

    # Horizontal line
    y_pos -= 30
    pdf.line(margin, y_pos, width - margin, y_pos)

    # Signature fields
    y_pos -= 40
    pdf.drawString(label_x-25, y_pos, "Signature of the Secretary:")
    y_pos -= 30
    pdf.drawString(label_x-25, y_pos, "Signature of the Faculty Advisor:")

    # Save the generated PDF
    pdf.save()

    # Write the PDF to the specified filepath
    buffer.seek(0)
    with open(filepath, "wb") as f:
        f.write(buffer.read())

@app.route('/workshop-info', methods=['GET', 'POST'])
def workshop_info():
    if request.method == 'POST':
        # Collect event details and store in session
        workshop_details = {
            'association_name': request.form['association_name'],
            'workshop_name': request.form['workshop_name']
        }
        session['workshop_info'] = workshop_details
        return redirect(url_for('workshop_instruction'))

    return render_template('workshop_info.html')
@app.route('/workshop_instruction', methods=['GET', 'POST'])
def workshop_instruction():
    if request.method == 'POST':
        return redirect(url_for('workshop_detail'))
    return render_template('workshop_instruction.html')
@app.route('/workshop-detail', methods=['GET', 'POST'])
def workshop_detail():
    if request.method == 'POST':
        # Collect event details and store in session
        workshop_details = {
            'secretary_name': request.form['secretary_name'],
            'secretary_roll_number': request.form['secretary_roll_number'],
            'secretary_mobile': request.form['secretary_mobile'],
            'convenor_name': request.form['convenor_name'],
            'convenor_roll_number': request.form['convenor_roll_number'],
            'convenor_mobile': request.form['convenor_mobile'],
            'faculty_advisor_name': request.form['faculty_advisor_name'],
            'faculty_advisor_designation': request.form['faculty_advisor_designation'],
            'faculty_advisor_contact': request.form['faculty_advisor_contact'],
            'speaker_name': request.form['speaker_name'],
            'speaker_designation': request.form['speaker_designation'],
            'speaker_contact': request.form['speaker_contact']
        }
        session['workshop_details'] =workshop_details
        return redirect(url_for('workshop_page'))
    return render_template('workshop_detail.html')

@app.route('/workshop', methods=['GET', 'POST'])
def workshop_page():
    if request.method == 'POST':
        # Collect event data and store in session
        workshop_data = {
            'day_2': 'day_1' in request.form,
            'day_3': 'day_2' in request.form,
            'both_days': 'both_days' in request.form,
            'participants': request.form.get('participants'),
            'halls_required': request.form.get('halls_required'),
            'preferred_halls': request.form.get('preferred_halls'),
            'slot': request.form.get('slot'),
            'extension_boxes': request.form.get('extension_boxes'),
        }
        session['workshop_data'] = workshop_data
        return redirect(url_for('items_ws'))
    return render_template('workshop.html')
@app.route('/items_ws', methods=['GET', 'POST'])
def items_ws():
    
    if 'workshop_items' not in session:
        session['workshop_items'] = []

    if request.method == 'POST':
        # Collect item data from the form and store it in the session
        try:
            items_data = {
                "sno": request.form.get("sno"),
                "item_name": request.form.get("item_name"),
                "quantity": int(request.form.get("quantity")),
                "price_per_unit": float(request.form.get("price_per_unit")),
                "total_price": int(request.form.get("quantity")) * float(request.form.get("price_per_unit"))
            }

            # Validate required fields
            if not items_data["item_name"] or not items_data["quantity"]:
                flash("Item name and quantity are required.")
                return redirect(url_for('items_ws'))

            # Append item to session
            session['workshop_items'].append(items_data)
            flash("Item added successfully!")
            return redirect(url_for('workshop_summary'))
        except ValueError:
            flash("Please enter valid numeric values for quantity and price.")
            return redirect(url_for('items_ws'))

    return render_template('items_ws.html', workshop_items=session['workshop_items'])
@app.route('/workshop_summary', methods=['GET', 'POST'])
def workshop_summary():
    if request.method == 'POST':
        # Collect workshop general information
        workshop_name = request.form.get('workshop_name')
        description = request.form.get('workshop_description')
        prerequisites = request.form.get('workshop_prerequisites')
        
        # Initialize sessions list
        sessions = []

        # Get the number of sessions (from the input field in the HTML)
        session_count = int(request.form.get('session_count', 0))

        # Collect session details (session number, time, topic, and description)
        for i in range(session_count):
            sessions.append({
                "session_no": request.form.get(f'session_no_{i}'),
                "session_time": request.form.get(f'session_time_{i}'),
                "session_topic": request.form.get(f'session_topic_{i}'),
                "session_description": request.form.get(f'session_description_{i}')
            })

        # Store the workshop data in the session or database (depending on how you want to save it)
        session['workshop_summary'] = {
            "workshop_name": workshop_name,
            "description": description,
            "prerequisites": prerequisites,
            "sessions": sessions
        }

        # Redirect to the preview page (assuming a route named 'preview' exists)
        return redirect(url_for('preview_ws'))

    # If the method is GET, render the workshop form template
    return render_template('workshop_form.html')
@app.route('/preview_ws', methods=['GET'])
def preview_ws():
    try:
        # Retrieve workshop details, workshop data, workshop items, and workshop form data from session
        workshop_details = session.get('workshop_details', {})
        workshop_data = session.get('workshop_data', {})
        workshop_items = session.get('workshop_items', [])
        workshop_form_data = session.get('workshop_form_data', {})
        # if not workshop_items:
        #     flash("No items found.")
        # return redirect(url_for('items_ws_page')) 

        # Pass all the data to the template
        return render_template('preview_ws.html', 
                               workshop_details=workshop_details, 
                               workshop_data=workshop_data,
                               workshop_items=workshop_items,
                               workshop_form_data=workshop_form_data)
    except Exception:
        return jsonify({"status": "error", "message": "Error retrieving preview data"}), 500
@app.route('/submit_ws_event', methods=['POST'])
def submit_ws_event():
    try:
        # Get the request JSON data
        all_workshop_data = request.get_json()  # Correct method to get JSON data
        workshop_details = all_workshop_data.get('workshopDetails')
        workshop_data = all_workshop_data.get('workshopData')
        workshop_items = all_workshop_data.get('workshopItems')  # Correct field name should match
        workshop_summary = all_workshop_data.get('workshopFormData')
        association_name=all_workshop_data.get('association_name')
        workshop_name=all_workshop_data.get('workshop_name')

        # Log the received data to ensure it's correct
        print("Received event details:", workshop_details)
        print("Received event data:", workshop_data)
        print("Received event items:", workshop_items)  # Log items
        print("Received event summary:", workshop_summary)

        # Generate a new event ID based on the last event ID in the database
        existing_workshop = workshop_collection.find_one(sort=[("workshop_id", -1)])
        if existing_workshop and "event_id" in existing_workshop:
            last_workshop_num = int(existing_workshop["workshop_id"][4:])
            new_workshop_id = f"WKSP{last_workshop_num + 1:02d}"
        else:
            new_workshop_id = "WKSP01"

        # Prepare the event entry for the database
        workshop_entry = {
            "workshop_id": new_workshop_id,
            "details": workshop_details,
            "workshop": workshop_data,
            "items": workshop_items,
            "form": workshop_summary,
            "association_name":association_name,
            "workshop_name":workshop_name
        }
        print("Event Entry to be inserted:", workshop_entry)
        
        # Insert data into the database
        workshop_collection.insert_one(workshop_entry)

        session["workshop_id"] = new_workshop_id

        return jsonify({"status": "success", "message": "Event submitted successfully!", "workshop_id": new_workshop_id}), 200

    except Exception as e:
        print("Error during event submission:", str(e))
        return jsonify({"status": "error", "message": str(e)}), 500
    
@app.route('/confirm_ws')
def confirm_ws_page():
    workshop_id=session.get("workshop_id")
    return render_template('confirm_ws.html',workshop_id=workshop_id)









if __name__ == '__main__':
    app.run(debug=True)

