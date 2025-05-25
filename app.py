"""
Gradio app for the Social Support Application Processing System.
"""
import re
import uuid
import gradio as gr
import os
import tempfile
import logging
from typing_extensions import List, Tuple, Optional
from datetime import datetime
from models.data_models import *

from workflow.graph import create_workflow_graph
from wrapper import process_application, process_query
from database.db_operations import initialize_database
from config import ASSETS_DIR, LOGS_DIR

# Create a timestamped log file name
timestamp = datetime.now().strftime("%d%m%Y_%H%M%S")
log_file = os.path.join(LOGS_DIR, f"app_{timestamp}.log")
# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize database
initialize_database()

class SocialSupportApp:
    """Main application class for the Social Support Processing System."""
    
    def __init__(self):
        self.chat_history = []
        self.temp_files = []
        self.app = create_workflow_graph()
        
    
    def cleanup_temp_files(self):
        """Clean up temporary files."""
        for file_path in self.temp_files:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                logger.warning(f"Could not remove temp file {file_path}: {e}")
        self.temp_files.clear()
    
    def save_uploaded_file(self, uploaded_file, applicantID) -> Optional[str]:
        """Save uploaded file to temporary location."""
        if uploaded_file is None:
            return None
        
        try:
            # Create temporary file
            temp_dir = tempfile.gettempdir()
            file_ext = os.path.splitext(uploaded_file.name)[1]
            temp_file = tempfile.NamedTemporaryFile(
                dir=temp_dir, 
                suffix=file_ext, 
                delete=False
            )
            
            # Copy content
            with open(uploaded_file.name, 'rb') as src:
                temp_file.write(src.read())
            
            with open(uploaded_file.name, 'rb') as src:
                with open(str(ASSETS_DIR / str(applicantID + "_" + uploaded_file.name.split("\\")[-1])), "wb") as f:
                    f.write(src.read())
            
            temp_file.close()
            self.temp_files.append(temp_file.name)
            return temp_file.name
        except Exception as e:
            logger.error(f"Error saving uploaded file: {e}")
            return None
    
    def process_chat_message(self, message: str, history: List[List[str]]) -> Tuple[str, List[List[str]]]:
        """Process chat message and return response."""
        if not message.strip():
            return "", history
        
        try:
            # Process query
            results = process_query(message, self.app)
            
            # Extract response from results
            if results and 'chatbot_conversation' in results:
                conversation = results['chatbot_conversation']
                # Find system response
                system_response = "I'm sorry, I couldn't process your request."
                for msg in conversation:
                    if msg.startswith("System: "):
                        system_response = msg.replace("System: ", "")
                        break
            else:
                system_response = "I'm sorry, I encountered an error while processing your request. Please try again."
            
            # Update history
            history.append([message, system_response])
            
        except Exception as e:
            logger.error(f"Error processing chat message: {e}")
            error_response = "I apologize, but I encountered an error. Please try again later."
            history.append([message, error_response])
        
        return "", history
    
    def submit_application(
        self,
        # Personal Information
        first_name: str,
        last_name: str,
        gender: str,
        emirates_id: str,
        address: str,
        # Financial Information
        monthly_income: float,
        assets: float,
        liabilities: float,
        household_size: int,
        age: int,
        education_level: str,
        marital_status: str,
        # Document uploads
        emirates_id_file,
        bank_statement_file,
        credit_report_file,
        resume_file,
        assets_liabilities_file,
        # Chat history
        history: List[List[str]]
    ) -> Tuple[List[List[str]], gr.update, str]:
        """Process application submission."""
        try:
            # Validate required fields
            if not all([first_name, last_name, emirates_id, monthly_income]):
                error_msg = "Please fill in all required fields (First Name, Last Name, Emirates ID, Monthly Income)."
                print(error_msg)
                return history, gr.update(visible=True), error_msg
            
            validate_emirates_id = lambda id: bool(re.match(r'^(\d{3}-\d{4}-\d{7}-\d{1}|\d{15})$', id.strip() if id else ''))
            if not validate_emirates_id:
                error_msg = "Emirates ID not in a valid format. Kindly, correct the format (XXX-XXXX-XXXXXXX-X)"
                print(error_msg)
                return history, gr.update(visible=True), error_msg

            # Validate file uploads
            required_files = [
                emirates_id_file, bank_statement_file, credit_report_file, 
                resume_file, assets_liabilities_file
            ]
            if not all(f is not None for f in required_files):
                error_msg = "Please upload all required documents."
                return history, gr.update(visible=True), error_msg
            
            applicant_id = str(uuid.uuid4())
            # Save uploaded files
            emirates_id_path = self.save_uploaded_file(emirates_id_file, applicant_id)
            bank_statement_path = self.save_uploaded_file(bank_statement_file, applicant_id)
            credit_report_path = self.save_uploaded_file(credit_report_file, applicant_id)
            resume_path = self.save_uploaded_file(resume_file, applicant_id)
            assets_liabilities_path = self.save_uploaded_file(assets_liabilities_file, applicant_id)
            if not all([emirates_id_path, bank_statement_path, credit_report_path, 
                       resume_path, assets_liabilities_path]):
                error_msg = "Error saving uploaded files. Please try again."
                return history, gr.update(visible=True), error_msg
            
            
            # Prepare application data
            application_data = {
                "applicant_id": applicant_id,
                'first_name': first_name,
                'last_name': last_name,
                'full_name': f"{first_name} {last_name}",
                'date_of_birth': "date_of_birth",
                'gender': gender,
                'nationality': "UAE",
                'emirates_id': emirates_id,
                'address': address,
                'monthly_income': monthly_income,
                'assets': assets,
                'liabilities': liabilities,
                'household_size': household_size,
                'age': age,
                'education_level': education_level,
                'marital_status': marital_status
            }
            
            # Process application
            results = process_application(
                emirates_id_path=emirates_id_path,
                bank_statement_path=bank_statement_path,
                credit_report_path=credit_report_path,
                resume_path=resume_path,
                assets_liabilities_path=assets_liabilities_path,
                application_data=application_data,
                use_cached_extraction=False,
                app =self.app,
                emirates_id_file=emirates_id_file.name, 
                bank_statement_file=bank_statement_file.name, 
                credit_report_file=credit_report_file.name, 
                resume_file=resume_file.name, 
                assets_liabilities_file=assets_liabilities_file.name
            )
            
            # Clean up temporary files
            self.cleanup_temp_files()
            
            # Prepare response message
            if "error" in results:
                response_msg = f"Application processing failed: {results['error']}"
            else:
                decision = results.get('decision', {}).get('decision', 'N/A')
                reason = results.get('decision', {}).get('reason', 'N/A')
                recommendations = results.get('recommendations', 'N/A')
                
                response_msg = f"""
                🎉 **Application Submitted Successfully!**
                
                **Decision:** {decision}
                
                **Reason:** {reason}
                
                **Recommendations:** {recommendations}
                
                Your application has been processed and saved to our system. You can now ask me questions about your application or the social support process.
                """
            
            # Add to chat history
            history.append([
                "I have submitted my social support application.",
                response_msg
            ])
            
            # Hide application form and show success message
            return history, gr.update(visible=False), "Application submitted successfully!"
            
        except Exception as e:
            logger.error(f"Error processing application: {e}")
            error_msg = f"An error occurred while processing your application: {str(e)}"
            return history, gr.update(visible=True), error_msg
    
    def show_application_form(self, history: List[List[str]]) -> Tuple[gr.update, List[List[str]]]:
        """Show the application form."""
        # Add message to chat history
        system_message = """
        📋 **Application Form Opened**
        
        Please fill out the application form that has appeared above. Make sure to:
        - Fill in all required personal and financial information
        - Upload all required documents (Emirates ID, Bank Statement, Credit Report, Resume, Assets & Liabilities spreadsheet)
        - Click 'Submit Application' when complete
        
        The form will close automatically after successful submission.
        """
        
        history.append([
            "I want to start a new application.",
            system_message
        ])
        
        return gr.update(visible=True), history
    
    def create_interface(self):
        """Create the Gradio interface."""

        
        with gr.Blocks(
            title="UAE Social Support Application System",
            theme=gr.themes.Soft(),
            css="""
            .gradio-container {max-width: 500px; margin: auto;}
            .chat-container {
                height: 500px;
            }
            """
        ) as interface:
            
            # Header
            gr.Markdown("""
            # 🇦🇪 UAE Social Support Application System
            
            Welcome to the UAE Government's Social Support Application Processing System. 
            You can chat with our AI assistant about social support programs or start a new application.
            """)
            
            # Chat Interface
            with gr.Row():
                with gr.Column(scale=4):

                    start_app_btn = gr.Button(
                        "🚀 Start New Application", 
                         variant="primary",
                        size="lg"
                    )

                    # Application Form (Initially Hidden)
                    with gr.Column(visible=False) as application_form:
                        gr.Markdown("## 📝 Social Support Application Form")
                        
                        with gr.Row():
                            with gr.Column():
                                gr.Markdown("### Personal Information")
                                first_name = gr.Textbox(
                                    label="First Name *", 
                                    placeholder="Enter your first name"
                                )
                                last_name = gr.Textbox(
                                    label="Last Name *", 
                                    placeholder="Enter your last name"
                                )
                                gender = gr.Dropdown(
                                    choices=["Male", "Female"],
                                    label="Gender"
                                )
                                emirates_id = gr.Textbox(
                                    label="Emirates ID *", 
                                    placeholder="784-YYYY-NNNNNNN-C"
                                )
                                address = gr.Textbox(
                                    label="Address", 
                                    placeholder="Enter your full address",
                                    lines=2
                                )
                            
                            with gr.Column():
                                gr.Markdown("### Financial Information")
                                monthly_income = gr.Number(
                                    label="Monthly Income (AED) *", 
                                    minimum=0,
                                    value=0
                                )
                                assets = gr.Number(
                                    label="Total Assets (AED)", 
                                    minimum=0,
                                    value=0
                                )
                                liabilities = gr.Number(
                                    label="Total Liabilities (AED)", 
                                    minimum=0,
                                    value=0
                                )
                                household_size = gr.Number(
                                    label="Household Size", 
                                    minimum=1,
                                    value=1,
                                    precision=0
                                )
                                age = gr.Number(
                                    label="Age", 
                                    minimum=18,
                                    maximum=100,
                                    value=25,
                                    precision=0
                                )
                                education_level = gr.Dropdown(
                                    choices=["uneducated", "high school", "bachelor's", "master's"],
                                    label="Highest Education Level",
                                    value="high school"
                                )
                                marital_status = gr.Dropdown(
                                    choices=["Single", "Married"],
                                    label="Marital Status",
                                    value="Single"
                                )
                        
                        gr.Markdown("### Document Uploads")
                        gr.Markdown("*Please upload all required documents in the specified formats*")
                        
                        with gr.Row():
                            with gr.Column():
                                emirates_id_file = gr.File(
                                    label="Emirates ID (Image: PNG, JPG, JPEG) *",
                                    file_types=[".png", ".jpg", ".jpeg"]
                                )
                                bank_statement_file = gr.File(
                                    label="Bank Statement (PDF) *",
                                    file_types=[".pdf"]
                                )
                                credit_report_file = gr.File(
                                    label="Credit Report (Image: PNG, JPG, JPEG, PDF) *",
                                    file_types=[".png", ".jpg", ".jpeg"]
                                )
                            
                            with gr.Column():
                                resume_file = gr.File(
                                    label="Resume/CV (PDF) *",
                                    file_types=[".pdf"]
                                )
                                assets_liabilities_file = gr.File(
                                    label="Assets & Liabilities Spreadsheet (Excel) *",
                                    file_types=[".xlsx", ".xls"]
                                )
                        
                        with gr.Row():
                            submit_app_btn = gr.Button(
                                "📤 Submit Application", 
                                variant="primary",
                                size="lg"
                            )
                            cancel_btn = gr.Button(
                                "❌ Cancel", 
                                variant="secondary"
                            )
                        
                        # Status message
                        status_msg = gr.Textbox(
                            label="Status",
                            interactive=False,
                            visible=False
                        )
                    

                    chatbot = gr.Chatbot(
                        label="Social Support Assistant",
                        height=400,
                        show_label=True,
                        container=True,
                        show_copy_button=True
                    )
                    
                    with gr.Row():
                        msg_input = gr.Textbox(
                            placeholder="Ask me about social support programs, eligibility criteria, or your application status...",
                            label="Your Message",
                            lines=2,
                            max_lines=5,
                            scale = 3
                        )
                        send_btn = gr.Button("Send", variant="primary")
                    
                    
            

            # Footer
            gr.Markdown("""
            ---
            *This system processes social support applications for UAE residents. 
            All information is handled securely and in accordance with UAE government policies.*
            """)
            
            # Event handlers
            def handle_send(message, history):
                return self.process_chat_message(message, history)
            
            def handle_start_application(history):
                return self.show_application_form(history)
            
            def handle_submit_application(*args):
                return self.submit_application(*args)
            
            def handle_cancel():
                return gr.update(visible=False), ""
            
            # Bind events
            send_btn.click(
                fn=handle_send,
                inputs=[msg_input, chatbot],
                outputs=[msg_input, chatbot]
            )
            
            msg_input.submit(
                fn=handle_send,
                inputs=[msg_input, chatbot],
                outputs=[msg_input, chatbot]
            )
            
            start_app_btn.click(
                fn=handle_start_application,
                inputs=[chatbot],
                outputs=[application_form, chatbot]
            )
            
            submit_app_btn.click(
                fn=handle_submit_application,
                inputs=[
                    first_name, last_name, gender,  
                    emirates_id, address, monthly_income, assets, liabilities, 
                    household_size, age, education_level, marital_status,
                    emirates_id_file, bank_statement_file, credit_report_file, 
                    resume_file, assets_liabilities_file, chatbot
                ],
                outputs=[chatbot, application_form, status_msg]
            )
            
            cancel_btn.click(
                fn=handle_cancel,
                outputs=[application_form, status_msg]
            )
        
        return interface

def main():
    """Main function to run the Gradio app."""
    app = SocialSupportApp()
    interface = app.create_interface()
    
    # Launch the app
    interface.launch(
        server_port=7860,
        share=False,
        debug=True,
        show_error=True,
        favicon_path=None,
        ssl_verify=False
    )

if __name__ == "__main__":
    main()