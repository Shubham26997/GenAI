import random
from fpdf import FPDF

# Initialize PDF
class InvoicePDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'B2B Invoice', border=0, ln=1, align='C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', align='C')

# Generate random invoice data
def generate_invoice_data():
    return {
        "invoice_number": f"INV-{random.randint(1000, 9999)}",
        "date": f"2026-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
        "buyer": f"Buyer {random.randint(1, 100)}",
        "seller": f"Seller {random.randint(1, 100)}",
        "gstin": f"{random.randint(10, 99)}ABCDE{random.randint(1000, 9999)}Z{random.randint(1, 9)}",
        "items": [
            {
                "description": f"Item {i}",
                "quantity": random.randint(1, 10),
                "price": random.randint(100, 1000),
            }
            for i in range(1, random.randint(2, 5))
        ],
    }

# Add invoice to PDF
def add_invoice_to_pdf(pdf, invoice):
    pdf.add_page()
    pdf.set_font('Arial', '', 12)

    pdf.cell(0, 10, f"Invoice Number: {invoice['invoice_number']}", ln=1)
    pdf.cell(0, 10, f"Date: {invoice['date']}", ln=1)
    pdf.cell(0, 10, f"Buyer: {invoice['buyer']}", ln=1)
    pdf.cell(0, 10, f"Seller: {invoice['seller']}", ln=1)
    pdf.cell(0, 10, f"GSTIN: {invoice['gstin']}", ln=1)

    pdf.ln(5)
    pdf.cell(0, 10, "Items:", ln=1)
    pdf.cell(80, 10, "Description", border=1)
    pdf.cell(30, 10, "Quantity", border=1)
    pdf.cell(30, 10, "Price", border=1)
    pdf.cell(30, 10, "Total", border=1)
    pdf.ln()

    for item in invoice['items']:
        total = item['quantity'] * item['price']
        pdf.cell(80, 10, item['description'], border=1)
        pdf.cell(30, 10, str(item['quantity']), border=1)
        pdf.cell(30, 10, f"{item['price']}", border=1)
        pdf.cell(30, 10, f"{total}", border=1)
        pdf.ln()

# Main function
def main():
    pdf = InvoicePDF()

    for _ in range(10000):
        invoice = generate_invoice_data()
        add_invoice_to_pdf(pdf, invoice)

    pdf.output("B2B_Invoices.pdf")

if __name__ == "__main__":
    main()