import re, uuid, base64, smtplib
from email.message import EmailMessage

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

def es_email_valido(email: str) -> bool:
    if not email: 
        return False
    return bool(EMAIL_REGEX.match(email.strip()))

def new_order_id() -> str:
    # ID corto para mostrar
    return uuid.uuid4().hex[:8].upper()

def enviar_email_pdf(destinatario: str, asunto: str, cuerpo_txt: str, nombre_pdf: str, pdf_bytes: bytes) -> tuple[bool, str]:
    """
    Envía un email con el PDF adjunto usando SMTP configurado en st.secrets.
    Retorna (ok, msg).
    Configura en .streamlit/secrets.toml:
      SMTP_HOST="smtp.gmail.com"
      SMTP_PORT=587
      SMTP_USER="tucuenta@gmail.com"
      SMTP_PASS="tu_app_password"
      SMTP_FROM="FRUTAS WC <tucuenta@gmail.com>"
    """
    try:
        host = st.secrets.get("SMTP_HOST", "")
        port = int(st.secrets.get("SMTP_PORT", 587))
        user = st.secrets.get("SMTP_USER", "")
        password = st.secrets.get("SMTP_PASS", "")
        sender = st.secrets.get("SMTP_FROM", user)

        if not all([host, port, user, password, sender]):
            return False, "SMTP no configurado en st.secrets."

        msg = EmailMessage()
        msg["Subject"] = asunto
        msg["From"] = sender
        msg["To"] = destinatario
        msg.set_content(cuerpo_txt)

        # Adjuntar PDF
        msg.add_attachment(pdf_bytes, maintype="application", subtype="pdf", filename=nombre_pdf)

        with smtplib.SMTP(host, port) as server:
            server.starttls()
            server.login(user, password)
            server.send_message(msg)

        return True, "Email enviado."
    except Exception as e:
        return False, f"Fallo al enviar email: {e}"
