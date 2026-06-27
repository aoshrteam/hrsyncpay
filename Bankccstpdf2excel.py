import os
import re
from tkinter import Tk, filedialog, messagebox, simpledialog
import camelot
import pandas as pd
from pypdf import PdfReader, PdfWriter


def decrypt_pdf_if_needed(pdf_path):
    """Checks if a PDF is encrypted and prompts the user for the password."""
    reader = PdfReader(pdf_path)

    if not reader.is_encrypted:
        return pdf_path  # Return original path if it's already unlocked

    # Prompt user for password via a popup box
    root = Tk()
    root.withdraw()
    password = simpledialog.askstring(
        "Password Required",
        f"The file '{os.path.basename(pdf_path)}' is password protected.\n"
        "Please enter the PDF password (e.g., your HDFC Customer ID):",
        show="*",
    )
    root.destroy()

    if not password:
        return None

    try:
        reader.decrypt(password)
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)

        decrypted_path = pdf_path.replace(".pdf", "_unlocked_temp.pdf")
        with open(decrypted_path, "wb") as f:
            writer.write(f)
        return decrypted_path
    except Exception as e:
        print(f"Decryption failed: {e}")
        return None


def clean_credit_card_data(df):
    """Filters out summary boxes and extracts actual transaction rows."""
    if df.empty:
        return df

    # Regex pattern to match typical statement dates (e.g., 12/25, 12-25, 12 Jan)
    date_pattern = re.compile(
        r"^\d{2}[/\-]\d{2}|\d{2}\s[A-Za-z]{3}|\d{2}[/\-]\d{2}[/\-]\d{2,4}"
    )

    valid_rows = []
    for _, row in df.iterrows():
        # Check if the first or second column contains a transaction date
        col1 = str(row.iloc[0]).strip()
        col2 = str(row.iloc[1]).strip() if len(row) > 1 else ""

        if date_pattern.match(col1) or date_pattern.match(col2):
            valid_rows.append(row)

    if valid_rows:
        return pd.DataFrame(valid_rows)
    return df  # Fallback to full data if filtering logic doesn't catch rows


def master_statement_utility():
    # 1. Select File
    root = Tk()
    root.withdraw()
    pdf_path = filedialog.askopenfilename(
        title="Select Bank or Credit Card Statement",
        filetypes=[("PDF Files", "*.pdf")],
    )
    if not pdf_path:
        return

    # 2. Handle Encryption
    processed_pdf = decrypt_pdf_if_needed(pdf_path)
    if not processed_pdf:
        messagebox.showerror(
            "Error", "Could not process file: Incorrect or missing password."
        )
        return

    # 3. Select Save Location
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    excel_path = filedialog.asksaveasfilename(
        title="Save Excel File As",
        initialfile=f"{base_name}_cleaned",
        defaultextension=".xlsx",
        filetypes=[("Excel Files", "*.xlsx")],
    )
    if not excel_path:
        # Cleanup temporary decrypted file if it was created
        if processed_pdf != pdf_path and os.path.exists(processed_pdf):
            os.remove(processed_pdf)
        return

    try:
        print("Extracting layout tables...")
        # 'stream' handles most credit card text block layouts flawlessly
        tables = camelot.read_pdf(processed_pdf, pages="all", flavor="stream")

        if len(tables) == 0:
            tables = camelot.read_pdf(
                processed_pdf, pages="all", flavor="lattice"
            )

        if len(tables) > 0:
            # Combine raw data
            raw_df = pd.concat([table.df for table in tables], ignore_index=True)

            # Route to smart filter to remove summary boxes/meta headers
            final_df = clean_credit_card_data(raw_df)

            # Export clean file
            final_df.to_excel(excel_path, index=False, header=False)

            messagebox.showinfo("Success", f"File saved to:\n{excel_path}")
        else:
            messagebox.showwarning("Notice", "No structured tables detected.")

    except Exception as e:
        messagebox.showerror("Extraction Error", f"Failed to parse PDF:\n{e}")
    finally:
        # Final cleanup of decrypted temporary file
        if processed_pdf != pdf_path and os.path.exists(processed_pdf):
            os.remove(processed_pdf)


if __name__ == "__main__":
    master_statement_utility()