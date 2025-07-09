# app.py

import os
import streamlit as st
from io import StringIO
from typing import Optional

# For reading PDF and DOCX
from PyPDF2 import PdfReader
import docx2txt

import requests

# Constants
SUPPORTED_EXTENSIONS = ["pdf", "docx", "txt"]

st.set_page_config(page_title="Job Application Assistant", layout="centered")


def extract_text_from_pdf(file) -> str:
    try:
        reader = PdfReader(file)
        text = []
        for page in reader.pages:
            text.append(page.extract_text() or "")
        return "\n".join(text).strip()
    except Exception:
        return ""


def extract_text_from_docx(file) -> str:
    try:
        # docx2txt expects a file path or file-like object, here file-like object works
        text = docx2txt.process(file)
        return text.strip() if text else ""
    except Exception:
        return ""


def extract_text_from_txt(file) -> str:
    try:
        text = file.read().decode("utf-8")
        return text.strip()
    except Exception:
        return ""


def extract_cv_text(uploaded_file) -> Optional[str]:
    if not uploaded_file:
        return None

    ext = uploaded_file.name.split(".")[-1].lower()

    if ext not in SUPPORTED_EXTENSIONS:
        st.error(f"Unsupported file type: {ext}. Please upload PDF, DOCX, or TXT.")
        return None

    if ext == "pdf":
        text = extract_text_from_pdf(uploaded_file)
    elif ext == "docx":
        # docx2txt requires a file path or file-like object that supports seek
        uploaded_file.seek(0)
        text = extract_text_from_docx(uploaded_file)
    elif ext == "txt":
        uploaded_file.seek(0)
        text = extract_text_from_txt(uploaded_file)
    else:
        text = None

    if not text:
        st.warning("No text extracted from the uploaded CV file.")
    return text


def call_gemini_api(prompt: str, api_key: str) -> Optional[str]:
    # NOTE: This is a placeholder for the Gemini API call.
    # Replace URL, headers, and payload according to actual Gemini API specs.
    # Here we simulate a POST request with the prompt.

    url = "https://gemini.api.example.com/v1/generate"  # Replace with real endpoint
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "prompt": prompt,
        "max_tokens": 500,
        "temperature": 0.7,
        "model": "gemini-1",
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
        # Assume the response JSON has a field like "generated_text"
        generated_text = data.get("generated_text")
        if not generated_text:
            st.error("API returned no generated text.")
            return None
        return generated_text.strip()
    except requests.exceptions.RequestException as e:
        st.error(f"API request failed: {e}")
        return None
    except ValueError:
        st.error("Failed to decode API response.")
        return None


def build_prompt(cv_text: str, job_desc: str) -> str:
    return (
        "You are a helpful assistant that writes a professional, tailored cover letter "
        "based on the candidate's CV or skills and the job description provided.\n\n"
        "Candidate's CV / Skills and Experience:\n"
        f"{cv_text}\n\n"
        "Job Description:\n"
        f"{job_desc}\n\n"
        "Write a tailored cover letter for this job application."
    )


def main():
    st.title("Job Application Assistant")
    st.header("Generate your tailored cover letter")

    st.markdown(
        """
        Upload your CV (PDF, DOCX, or TXT) **or** type your skills and experience below.
        Then paste the job description and generate your cover letter.
        """
    )

    cv_file = st.file_uploader(
        "Upload your CV (PDF, DOCX, TXT)", type=SUPPORTED_EXTENSIONS, help="Upload your CV file"
    )

    cv_text_input = st.text_area(
        "Or type your skills and experience here",
        height=150,
        placeholder="E.g., 5 years experience in software development, skilled in Python, JavaScript..."
    )

    job_description = st.text_area(
        "Paste the job description here",
        height=200,
        placeholder="Copy and paste the full job description..."
    )

    generate_btn = st.button("Generate Cover Letter")

    if generate_btn:
        # Get the API key from environment variable
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            st.error("Gemini API key not found. Please set the GEMINI_API_KEY environment variable.")
            return

        # Extract CV text
        if cv_file:
            cv_text = extract_cv_text(cv_file)
        else:
            cv_text = cv_text_input.strip()

        if not cv_text:
            st.warning("Please provide your CV text or type your skills and experience.")
            return

        if not job_description.strip():
            st.warning("Please provide the job description.")
            return

        with st.spinner("Generating cover letter..."):
            prompt = build_prompt(cv_text, job_description.strip())
            cover_letter = call_gemini_api(prompt, api_key)

        if cover_letter:
            st.subheader("Generated Cover Letter")
            st.text_area("Your Cover Letter", value=cover_letter, height=300)

            # Button to download the cover letter as a text file
            st.download_button(
                label="Download Cover Letter",
                data=cover_letter,
                file_name="cover_letter.txt",
                mime="text/plain",
            )


if __name__ == "__main__":
    main()
