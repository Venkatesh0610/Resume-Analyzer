import base64
import os
from analyzer import pdf_to_jpg, process_image  # Import image processing functions
import streamlit as st
import pandas as pd
import plotly.express as px


# Set page layout to "wide"
st.set_page_config(layout="wide")

# Page Navigation State
if "page" not in st.session_state:
    st.session_state.page = "main"

# Function to display project title
def show_project_title():
    st.markdown(
        """
        <h2 style="text-align: center; color: #4A90E2;">AI-Powered Resume Matcher</h2>
        """,
        unsafe_allow_html=True
    )


def show_loading_screen():
    """Displays a full-screen loading spinner while processing."""
    placeholder = st.empty()  # Create a placeholder for the spinner

    with placeholder.container():
        st.markdown(
            """
            <div style="position: fixed; top: 0; left: 0; width: 100%; height: 100%;
                        background-color: rgba(0, 0, 0, 0.8); display: flex; justify-content: center;
                        align-items: center; color: white; font-size: 24px; font-weight: bold;">
                ⏳ Analyzing your resume... Please wait.
            </div>
            """,
            unsafe_allow_html=True
        )

    return placeholder  # Return the placeholder so it can be removed later
# Callback function to remove resume
def remove_resume():
    st.session_state.resume_uploaded = False
    st.session_state.uploaded_file = None
    st.rerun()

# Function to save uploaded file to root directory
def save_uploaded_file(uploaded_file):
    file_path = os.path.join(os.getcwd(), uploaded_file.name)  # Save in root directory
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path  # Return file path


# Function to display analytics page with extracted data
def show_analytics():
    show_project_title()  # Keep title on analytics page

    st.title("📊 Resume & Job Description Analytics")

    # Check if extracted data is available
    if "extracted_data" in st.session_state and st.session_state.extracted_data:
        extracted_data = st.session_state.extracted_data  # Retrieve JSON data

        # Display Matching Score
        overall_score = extracted_data.get("overall_score", 0)
        st.subheader(f"Matching Score: {overall_score}%")

        # **Gauge Chart for Score Visualization**
        fig = px.bar(
            x=[overall_score], y=["Resume Match"],
            orientation="h", text=[f"{overall_score}%"],
            color_discrete_sequence=[
                "#2ECC71" if overall_score >= 80 else "#F39C12" if overall_score >= 60 else "#E74C3C"]
        )
        fig.update_traces(textposition="inside")
        fig.update_layout(xaxis=dict(range=[0, 100]), height=150, width=500)
        st.plotly_chart(fig, use_container_width=True)

        # Key Insights
        st.subheader("🔍 Key Insights")
        st.write(f"✅ Your resume matches **{overall_score}%** with the job description.")

        if overall_score >= 80:
            st.success("✅ Your resume **strongly aligns** with the job requirements! 🎯")
        elif overall_score >= 60:
            st.warning("⚠️ Your resume **partially aligns** with the job description. Consider improving a few areas.")
        else:
            st.error("🚨 Your resume needs **significant improvements** to match the job description.")

        # **Top Matching Skills Section**
        st.subheader("✅ Top Matching Skills")
        matching_skills = extracted_data.get("keyword_matching", [])
        top_matching = matching_skills[:5]
        remaining_matching = matching_skills[5:]

        if top_matching:
            st.success(", ".join(top_matching))  # Show top 5 matched skills
        else:
            st.warning("No matching skills found.")

        if remaining_matching:
            with st.expander(f"🔽 View all matched skills ({len(matching_skills)})"):
                st.write(", ".join(remaining_matching))

        # **Top Missing Skills Section**
        st.subheader("⚠️ Top Missing Skills")
        missing_skills = extracted_data.get("missing_keywords", [])
        top_missing = missing_skills[:5]
        remaining_missing = missing_skills[5:]

        if top_missing:
            st.error(", ".join(top_missing))  # Show top 5 missing skills
        else:
            st.success("Great! No critical missing skills.")

        if remaining_missing:
            with st.expander(f"🔽 View all missing skills ({len(missing_skills)})"):
                st.write(", ".join(remaining_missing))

        # **Categorized Improvements (Dynamic Sections)**
        st.subheader("📌 Categorized Improvements")

        suggestions = extracted_data.get("suggestions", [])

        # **important_keys dynamically categorizes suggestions**
        important_keys = {
            "Skills & Certifications": ["skill", "certification", "training"],
            "Experience & Work History": ["experience", "projects", "work history"],
            "Resume Formatting & Structure": ["format", "layout", "structure", "design"],
            "Education & Qualifications": ["education", "degree", "qualification"]
        }

        categorized_suggestions = {category: [] for category in important_keys.keys()}

        # **Classify suggestions dynamically**
        for suggestion in suggestions:
            for category, keywords in important_keys.items():
                if any(word in suggestion.lower() for word in keywords):
                    categorized_suggestions[category].append(f"🔹 {suggestion}")
                    break  # Stop checking further categories once assigned

        # **Display suggestions in expandable sections**
        for category, items in categorized_suggestions.items():
            if items:  # Only show category if it has items
                with st.expander(f"📌 {category} ({len(items)})"):
                    for item in items:
                        st.markdown(item)

        if not any(categorized_suggestions.values()):
            st.success("No major improvements needed. Well done!")

        # **High-Priority Improvement Suggestions Table with Color Coding**
        st.write("### 🚀 High-Priority Improvement Suggestions")

        priority_data = []
        for suggestion in suggestions:
            if "experience" in suggestion.lower():
                priority = "High"
                color = "🔴"  # Red for High Priority
            elif "skill" in suggestion.lower():
                priority = "Medium"
                color = "🟠"  # Orange for Medium Priority
            else:
                priority = "Low"
                color = "🟢"  # Green for Low Priority

            priority_data.append({
                "Improvement Suggestion": suggestion,
                "Priority": f"{color} {priority}"
            })

        priority_df = pd.DataFrame(priority_data)
        priority_df = priority_df.sort_values(by="Priority", ascending=False).head(
            5)  # Show top 5 high-priority improvements

        # **Styled Table for Perfect UI Alignment**
        st.dataframe(priority_df, use_container_width=True)

    else:
        st.error("No extracted data available. Please upload a resume first.")

    # Add spacing and navigation button
    st.markdown("<br>", unsafe_allow_html=True)
    col_center = st.columns([1, 2, 1])[1]
    with col_center:
        if st.button("🔙 Back to Upload", use_container_width=True):
            st.session_state.page = "main"
            st.rerun()


# Main Page: Job Description Input & Resume Upload
if st.session_state.page == "main":
    show_project_title()  # Show title at the top

    # Create two equal columns for Job Description & Resume Upload
    col1, col2 = st.columns([1, 1], gap="medium")

    # Left Column: Job Description Input
    with col1:
        st.subheader("Enter Job Description")
        job_description = st.text_area("Paste the job description here", height=400)

    # Right Column: Resume Uploader & PDF Viewer
    with col2:
        if "resume_uploaded" not in st.session_state:
            st.session_state.resume_uploaded = False
            st.session_state.uploaded_file = None

        if not st.session_state.resume_uploaded:
            st.subheader("Upload Resume")
            uploaded_file = st.file_uploader("Upload your PDF Resume", type=["pdf"])

            if uploaded_file is not None:
                file_path = save_uploaded_file(uploaded_file)  # Save file to root dir
                st.session_state.resume_uploaded = True
                st.session_state.uploaded_file = uploaded_file
                st.session_state.file_path = file_path
                st.rerun()

        if st.session_state.resume_uploaded and st.session_state.uploaded_file:
            # Convert PDF to Base64 for preview
            def get_pdf_base64(file_path):
                with open(file_path, "rb") as file:
                    base64_pdf = base64.b64encode(file.read()).decode("utf-8")
                return f"data:application/pdf;base64,{base64_pdf}"

            pdf_data = get_pdf_base64(st.session_state.file_path)

            # Display PDF with Close Button
            st.subheader("Uploaded Resume")

            # Add some vertical space before showing the PDF preview
            st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)

            # Create two columns: PDF preview | Close button on the same row
            col3, col4 = st.columns([10, 1])
            with col3:
                st.markdown(
                    f'<iframe src="{pdf_data}" width="100%" height="400" style="border: none; margin-top: 15px;"></iframe>',
                    unsafe_allow_html=True,
                )
            with col4:
                if st.button("❌", key="remove_resume", help="Remove Resume", use_container_width=True):
                    remove_resume()

    # Check if both Job Description & Resume are uploaded
    is_analyze_enabled = bool(job_description.strip()) and st.session_state.resume_uploaded

    # Centered "Analyze Resume" Button Below Preview
    st.markdown("<br>", unsafe_allow_html=True)  # Add space
    col_center = st.columns([1, 2, 1])[1]  # Center column
    with col_center:
        if st.button("🔍 Analyze Resume", use_container_width=True, disabled=not is_analyze_enabled):
            if is_analyze_enabled:
                loading_placeholder = show_loading_screen()  # Show full-screen loading

                try:
                    st.session_state.page = "analytics"

                    # Ensure the file is saved before processing
                    file_path = st.session_state.file_path

                    # Convert PDF to Images
                    image_paths = pdf_to_jpg(file_path)  # Pass file path to function

                    # Extracted text storage
                    extracted_text = []

                    # Update prompt to analyze full resume text
                    prompt = f"""
                    Extract the text present in the image, and provide the result in JSON format.
                    """

                    # Process each image using AI
                    for img_path in image_paths:
                        result = process_image(file_path=img_path, prompt=prompt,
                                               type="image")  # Assuming it returns a dict
                        extracted_text.append(result)

                    print(extracted_text)

                    # Update prompt to analyze full resume text
                    final_prompt = f"""
                    You are an AI-powered Resume Analyzer Assistant. Your task is to evaluate a user's resume against a given job description and generate structured insights.
                    
                    ----------------------------------------------
                    
                    ### **Job Description:**  
                    {job_description}

                    ----------------------------------------------

                    ### ** Extracted Text:**
                    {extracted_text}
                    
                    ----------------------------------------------
                    
                    ### **Analysis Requirements:**  
                    Analyze the entire extracted resume against the provided job description and generate a concise, structured report with the following:

                    Overall Resume Score (out of 100) – Measure alignment with the job description.
                    Matching Skills – Extract only those skills present in both the resume and job description (exclude irrelevant skills).
                    Missing Skills – Identify job-required skills that are missing from the resume.
                    Precise Suggestions – Provide short, specific improvement points only based on job requirements (avoid generic advice).
                    Key Focus Areas – List the most critical elements from the job description that need attention.
                    Ensure that the response is structured, clear, and formatted in JSON for easy processing. Use the below JSON key as reference:

                    ```json
                    
                        "overall_score": 50,
                        "keyword_matching": ["python", "java"],
                        "missing_keywords": ["sql", "db"],
                        "suggestions": ["add more skills"],
                        "important_keys":["experience","format","certifications"]
                    ```
                    """

                    # Send final prompt to AI for analysis
                    final_result = process_image(file_path=extracted_text, prompt=final_prompt,
                                                 type="text")  # Use first page image to trigger analysis

                    # Store extracted data in session state
                    st.session_state.extracted_data = final_result  # Parse JSON response

                finally:
                    loading_placeholder.empty()  # Remove the loading screen

                # Redirect to analytics page
                st.rerun()

# Show Analytics Page
elif st.session_state.page == "analytics":
    show_analytics()
