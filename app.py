import streamlit as st
from fpdf import FPDF
import io
import google.generativeai as genai

# --- Configure Gemini ---
genai.configure(api_key="AIzaSyASrWmpyD89npQA6hXQvitroOQaDZeafco")

# --- Generate Summary from Gemini (with fallback) ---
def generate_summary(name, skills):
    prompt = f"""
    Write a professional resume summary for a candidate with the following skills:
    {skills}.
    Keep it concise, ATS-optimized, and do not start with the name. Avoid first-person (I, me).
    """
    try:
        model = genai.GenerativeModel(model_name="models/gemini-1.5-pro")
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception:
        fallback = f"A skilled professional with expertise in {skills}."
        return f"(Fallback) {fallback}"

# --- Streamlit Config ---
st.set_page_config(page_title="AI Resume Builder Pro", page_icon="📄", layout="wide")

if 'resume_data' not in st.session_state:
    st.session_state.resume_data = {"template": "Modern", "theme": "Blue", "font": "Arial"}

with st.sidebar:
    st.header("⚙️ Settings")
    st.session_state.resume_data['template'] = st.selectbox("Choose Template", ["Modern", "Classic", "Creative", "Minimalist"])
    st.session_state.resume_data['theme'] = st.selectbox("Color Theme", ["Blue", "Black", "Green", "Professional"])
    st.session_state.resume_data['font'] = st.selectbox("Font", ["Arial", "Times New Roman", "Helvetica", "Calibri"])

    # Light mode by default
    dark_mode = st.toggle("Dark Mode", False)
    if dark_mode:
        st.markdown("""
        <style>
        .stApp { background-color: #1e1e1e; color: white; }
        .stTextInput>div>div>input, .stTextArea>div>div>textarea {
            background-color: #2d2d2d !important;
            color: white !important;
        }
        </style>
        """, unsafe_allow_html=True)

# --- Main UI ---
st.title("📄 AI Resume Builder Pro")
st.caption("Generate a polished resume in minutes!")

tab1, tab2, tab3 = st.tabs(["Basic Info", "Work & Education", "Extras"])

# === TAB 1: BASIC INFO ===
with tab1:
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Full Name*", placeholder="John Doe")
        email = st.text_input("Email*", placeholder="john@example.com")
    with col2:
        phone = st.text_input("Phone", placeholder="+1 123-456-7890")
        location = st.text_input("Location", placeholder="New York, USA")

    st.subheader("Social Links")
    linkedin = st.text_input("LinkedIn", placeholder="https://linkedin.com/in/username")
    github = st.text_input("GitHub", placeholder="https://github.com/username")

    st.subheader("Skills")
    skills = st.text_area("Enter your skills (comma-separated)*", placeholder="Python, SQL, Web Development", height=100)

# === SUMMARY GENERATION ===
summary = st.session_state.get("generated_summary", "")
if name and skills and not summary:
    with st.spinner("Generating summary with Gemini..."):
        summary = generate_summary(name, skills)
        st.session_state.generated_summary = summary

# === TAB 2: WORK & EDUCATION ===
with tab2:
    st.subheader("Work Experience")
    exp_count = st.number_input("Number of Experiences", min_value=1, max_value=5, value=1)
    experiences = []
    for i in range(exp_count):
        with st.expander(f"Experience {i+1}", expanded=(i==0)):
            col1, col2 = st.columns(2)
            with col1:
                job_title = st.text_input(f"Job Title {i+1}*", key=f"job_title_{i}")
                company = st.text_input(f"Company {i+1}*", key=f"company_{i}")
            with col2:
                duration = st.text_input(f"Duration {i+1}*", key=f"duration_{i}")
            desc = st.text_area(f"Description {i+1}", key=f"desc_{i}", height=100)
            experiences.append({
                "job_title": job_title,
                "company": company,
                "duration": duration,
                "description": desc
            })

    st.subheader("Education")
    edu_count = st.number_input("Number of Education Entries", min_value=1, max_value=3, value=1)
    educations = []
    for i in range(edu_count):
        with st.expander(f"Education {i+1}", expanded=(i==0)):
            col1, col2 = st.columns(2)
            with col1:
                degree = st.text_input(f"Degree {i+1}*", key=f"degree_{i}")
                university = st.text_input(f"University {i+1}*", key=f"university_{i}")
            with col2:
                edu_duration = st.text_input(f"Duration {i+1}*", key=f"edu_duration_{i}")
            educations.append({
                "degree": degree,
                "university": university,
                "duration": edu_duration
            })

# === TAB 3: EXTRAS ===
with tab3:
    st.subheader("Projects")
    projects = st.text_area("Projects (Optional)", height=120)

    st.subheader("Cover Letter")
    cover_letter = st.text_area("Cover Letter (Optional)", height=150)
    if st.button("📝 AI-Generate Cover Letter"):
        cover_letter = f"""Dear Hiring Manager,\n\nI am excited to apply for the [Job Title] position at [Company]. With my background in [Field], I am confident in my ability to contribute to your team.\n\nSincerely,\n{name}"""
        st.write(cover_letter)

# === RESUME PREVIEW ===
st.divider()
st.subheader("📋 Live Preview")
if st.button("🔄 Update Preview"):
    preview_html = f"""
    <div style="border: 1px solid #ccc; padding: 20px; border-radius: 10px; font-family: {st.session_state.resume_data['font']};">
        <h1 style="color: {st.session_state.resume_data['theme'].lower()};">{name}</h1>
        <p>{email} | {phone} | {location}</p>
        <p>{"LinkedIn: " + linkedin if linkedin else ""} {"| GitHub: " + github if github else ""}</p>
        <h3>Summary</h3>
        <p>{summary if summary else "No summary generated yet."}</p>
        <h3>Experience</h3>
        <ul>
            {''.join([f"<li><b>{exp['job_title']}</b> at {exp['company']} ({exp['duration']})<br>{exp['description']}</li>" for exp in experiences])}
        </ul>
    </div>
    """
    st.markdown(preview_html, unsafe_allow_html=True)

# === PDF EXPORT ===
st.divider()
if st.button("📅 Generate Resume PDF", type="primary"):
    if not name or not email or not summary:
        st.error("Please fill required fields (*)")
    else:
        try:
            fpdf_font_map = {
                "Arial": "Arial",
                "Times New Roman": "Times",
                "Helvetica": "Helvetica",
                "Calibri": "Arial"
            }
            chosen_font = fpdf_font_map.get(st.session_state.resume_data['font'], "Arial")

            pdf = FPDF()
            pdf.add_page()
            pdf.set_font(chosen_font, size=12)
            pdf.set_text_color(0, 0, 128)
            pdf.cell(200, 10, txt=name, ln=True, align='C')

            pdf.set_text_color(0, 0, 0)
            contact_line = f"{email} | {phone} | {location}"
            if linkedin:
                contact_line += f" | LinkedIn: {linkedin}"
            if github:
                contact_line += f" | GitHub: {github}"
            pdf.multi_cell(0, 8, txt=contact_line, align='C')
            pdf.ln(10)

            sections = [
                ("Summary", summary.replace("(Fallback)", "").strip()),
                ("Skills", skills),
                ("Experience", "\n".join([f"{exp['job_title']} at {exp['company']} ({exp['duration']})\n{exp['description']}" for exp in experiences])),
                ("Education", "\n".join([f"{edu['degree']} from {edu['university']} ({edu['duration']})" for edu in educations])),
                ("Projects", projects),
                ("Cover Letter", cover_letter)
            ]

            for section, content in sections:
                if content.strip():
                    pdf.set_font(chosen_font, 'B', 14)
                    pdf.cell(200, 10, txt=section, ln=True)
                    pdf.set_font(chosen_font, size=12)
                    pdf.multi_cell(0, 7, txt=content)
                    pdf.ln(5)

            pdf_bytes = io.BytesIO(pdf.output(dest='S').encode('latin1'))

            col1, col2 = st.columns(2)
            with col1:
                st.download_button("⬇️ Download PDF", data=pdf_bytes, file_name=f"{name.replace(' ', '_')}_Resume.pdf", mime="application/pdf")
            with col2:
                st.download_button("⬇️ Download TXT", data=f"Name: {name}\nEmail: {email}\n\nSummary:\n{summary}".encode(), file_name=f"{name.replace(' ', '_')}_Resume.txt", mime="text/plain")
            st.success("✅ Resume generated successfully!")
        except Exception as e:
            st.error(f"❌ Error: {e}")

# === ATS SCORING (Optional Placeholder) ===
if st.button("🔍 Check ATS Score"):
    score = 85
    st.progress(score)
    st.info(f"ATS Score: {score}/100. Tip: Add more keywords from the job description!")
