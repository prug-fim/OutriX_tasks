# invoice_app.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from decimal import Decimal, ROUND_HALF_UP
from fpdf import FPDF
from datetime import date
import uuid

def fmt_money(x):
    return f"₹{x:.2f}"

class InvoiceApp:
    def __init__(self, root):
        self.root = root
        root.title("Invoice Generator")
        self.items = []  # list of (desc, qty Decimal, unit Decimal)

        # Header frame
        hf = ttk.Frame(root, padding=8)
        hf.pack(fill="x")
        ttk.Label(hf, text="Invoice No:").grid(row=0, column=0, sticky="w")
        self.inv_no = ttk.Entry(hf)
        self.inv_no.grid(row=0, column=1, sticky="w")
        self.inv_no.insert(0, str(uuid.uuid4())[:8])

        ttk.Label(hf, text="Date:").grid(row=0, column=2, sticky="w", padx=(10,0))
        self.date_var = ttk.Entry(hf)
        self.date_var.grid(row=0, column=3, sticky="w")
        self.date_var.insert(0, date.today().isoformat())

        # Client / Company
        c = ttk.Frame(root, padding=8)
        c.pack(fill="x")
        ttk.Label(c, text="From (your company):").grid(row=0, column=0, sticky="w")
        self.from_entry = ttk.Entry(c, width=50)
        self.from_entry.grid(row=0, column=1, sticky="w")
        self.from_entry.insert(0, "Your Company Name\nAddress Line 1")

        ttk.Label(c, text="Bill To:").grid(row=1, column=0, sticky="w")
        self.to_entry = ttk.Entry(c, width=50)
        self.to_entry.grid(row=1, column=1, sticky="w")
        self.to_entry.insert(0, "Client Name\nClient Address")

        # Add item form
        form = ttk.Frame(root, padding=8)
        form.pack(fill="x")
        ttk.Label(form, text="Description").grid(row=0, column=0)
        ttk.Label(form, text="Qty").grid(row=0, column=1)
        ttk.Label(form, text="Unit Price").grid(row=0, column=2)
        self.desc = ttk.Entry(form, width=40)
        self.desc.grid(row=1, column=0)
        self.qty = ttk.Entry(form, width=8)
        self.qty.grid(row=1, column=1)
        self.unit = ttk.Entry(form, width=12)
        self.unit.grid(row=1, column=2)
        ttk.Button(form, text="Add Item", command=self.add_item).grid(row=1, column=3, padx=8)

        # Items display (Treeview)
        tvf = ttk.Frame(root, padding=8)
        tvf.pack(fill="both", expand=True)
        cols = ("desc","qty","unit","total")
        self.tree = ttk.Treeview(tvf, columns=cols, show="headings", height=8)
        for col in cols:
            self.tree.heading(col, text=col.capitalize())
        self.tree.column("desc", width=300)
        self.tree.column("qty", width=60)
        self.tree.column("unit", width=100)
        self.tree.column("total", width=100)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(tvf, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        # Totals and tax
        bottom = ttk.Frame(root, padding=8)
        bottom.pack(fill="x")
        ttk.Label(bottom, text="Tax %:").grid(row=0, column=0, sticky="w")
        self.tax_var = ttk.Entry(bottom, width=8)
        self.tax_var.grid(row=0, column=1, sticky="w")
        self.tax_var.insert(0, "18")  # default 18%

        ttk.Button(bottom, text="Remove Selected", command=self.remove_selected).grid(row=0, column=2, padx=8)
        ttk.Button(bottom, text="Generate PDF", command=self.generate_pdf).grid(row=0, column=3, padx=8)

        # summary labels
        sframe = ttk.Frame(root, padding=8)
        sframe.pack(fill="x")
        self.subt_label = ttk.Label(sframe, text="Subtotal: ₹0.00")
        self.subt_label.pack(anchor="e")
        self.tax_label = ttk.Label(sframe, text="Tax: ₹0.00")
        self.tax_label.pack(anchor="e")
        self.total_label = ttk.Label(sframe, text="Total: ₹0.00", font=("TkDefaultFont", 12, "bold"))
        self.total_label.pack(anchor="e")

    def add_item(self):
        d = self.desc.get().strip()
        try:
            q = Decimal(self.qty.get().strip())
            u = Decimal(self.unit.get().strip())
        except Exception:
            messagebox.showerror("Invalid", "Qty and Unit Price must be numeric.")
            return
        line_total = (q * u).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        self.items.append((d, q, u))
        self.tree.insert("", "end", values=(d, str(q), f"{u:.2f}", f"{line_total:.2f}"))
        self.desc.delete(0, "end"); self.qty.delete(0, "end"); self.unit.delete(0, "end")
        self.update_totals()

    def remove_selected(self):
        sel = self.tree.selection()
        if not sel:
            return
        for s in sel:
            idx = self.tree.index(s)
            self.tree.delete(s)
            del self.items[idx]
        self.update_totals()

    def update_totals(self):
        subtotal = Decimal("0.00")
        for d,q,u in self.items:
            subtotal += (q * u)
        subtotal = subtotal.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        try:
            tax_pct = Decimal(self.tax_var.get().strip()) / Decimal("100")
        except Exception:
            tax_pct = Decimal("0.00")
        tax = (subtotal * tax_pct).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        total = (subtotal + tax).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        self.subt_label.config(text=f"Subtotal: ₹{subtotal}")
        self.tax_label.config(text=f"Tax: ₹{tax}")
        self.total_label.config(text=f"Total: ₹{total}")

    def generate_pdf(self):
        if not self.items:
            messagebox.showerror("No items", "Add at least one item.")
            return
        savepath = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF","*.pdf")], title="Save invoice")
        if not savepath:
            return
        pdf = FPDF(format="A4")
        pdf.add_page()
        pdf.set_font("Helvetica", size=12)
        pdf.cell(0, 8, txt="INVOICE", ln=1, align="C")
        pdf.ln(4)
        # From / To
        pdf.set_font("Helvetica", size=10)
        pdf.multi_cell(0, 6, txt=f"From:\n{self.from_entry.get()}\n\nBill To:\n{self.to_entry.get()}")
        pdf.ln(2)
        pdf.cell(0,6,txt=f"Invoice No: {self.inv_no.get()}    Date: {self.date_var.get()}", ln=1)
        pdf.ln(4)
        # table header
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(90,8,"Description",1)
        pdf.cell(25,8,"Qty",1,align="R")
        pdf.cell(35,8,"Unit",1,align="R")
        pdf.cell(30,8,"Total",1,ln=1,align="R")
        pdf.set_font("Helvetica", size=10)
        subtotal = Decimal("0.00")
        for d,q,u in self.items:
            line_total = (q*u).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            pdf.cell(90,8,txt=d, border=1)
            pdf.cell(25,8,txt=str(q), border=1, align="R")
            pdf.cell(35,8,txt=f"{u:.2f}", border=1, align="R")
            pdf.cell(30,8,txt=f"{line_total:.2f}", border=1,ln=1, align="R")
            subtotal += line_total
        tax_pct = Decimal(self.tax_var.get().strip())/Decimal("100") if self.tax_var.get().strip() else Decimal("0")
        tax = (subtotal * tax_pct).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        total = (subtotal + tax).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        pdf.ln(4)
        pdf.cell(150,8,"Subtotal", align="R")
        pdf.cell(30,8,f"{subtotal:.2f}", ln=1, align="R")
        pdf.cell(150,8,f"Tax ({(tax_pct*100):.2f}%)", align="R")
        pdf.cell(30,8,f"{tax:.2f}", ln=1, align="R")
        pdf.set_font("Helvetica","B",11)
        pdf.cell(150,10,"Total", align="R")
        pdf.cell(30,10,f"{total:.2f}", ln=1, align="R")
        pdf.output(savepath)
        messagebox.showinfo("Saved", f"Invoice saved to {savepath}")

if __name__ == "__main__":
    root = tk.Tk()
    app = InvoiceApp(root)
    root.mainloop()
