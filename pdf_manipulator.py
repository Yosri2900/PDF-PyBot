from tkinter import Frame, Button, Label, Entry, Misc, Tk, ttk, filedialog, messagebox, END
from tkinter.simpledialog import Dialog
from PyPDF3 import PdfFileReader, PdfFileWriter
from re import match
import os

class CustomPagesDialog(Dialog):
    def __init__(self, parent: Misc, pdf_name: str, max_pages: int) -> None:
        self.pdf_name = pdf_name
        self.max_pages = max_pages
        super(CustomPagesDialog, self).__init__(parent, title="Edit")

    def body(self, master):
        Label(master, text=f"Number of Pages: {self.max_pages} - {self.pdf_name}").grid(row=0)
        self.custom_pages_entry = Entry(master)
        self.custom_pages_entry.grid(row=1, column=0)
        
    def validate(self):
        input_string = self.custom_pages_entry.get()
        pattern = r'^[0-9,-]*$'
        if match(pattern, input_string) is None:
            self.custom_pages_entry.config(bg='red')  # Change background color
            self.bell()  # Beep to indicate invalid input
            return False
        self.custom_pages_entry.config(bg='white')  # Reset background color
        return True
    
    def apply(self):
        self.result = self.custom_pages_entry.get()

selected_files = {}

def select_file():
    file_paths = filedialog.askopenfilenames(filetypes=[("PDF Files", "*.pdf")])
    for file_path in file_paths:
        file = os.path.basename(file_path)
        pages = count_pdf_pages(file_path)
        if file not in selected_files:
            if pages != -1:
                selected_files[file] = {
                    "Full Path": file_path,
                    "Start Page": 1,
                    "End Page": pages,
                    "Customized" : []
                }
                table.insert("", "end", values=(file, ""))

def count_pdf_pages(pdf_path):
    try:
        with open(pdf_path, "rb") as pdf_file:
            pdf_reader = PdfFileReader(pdf_file, strict=False)
            num_pages = pdf_reader.getNumPages()
            return num_pages
    except Exception:
        messagebox.showwarning("Reading Error", f"An error has occured. Cannot Read {pdf_path}")
        return -1

def delete_selected():
    elements = table.selection()
    for elem in elements:
        row = table.item(elem)
        selected_name = row.get("values")[0]
        selected_files.pop(selected_name, None)
        table.delete(elem)

def edit_custom_pages(event):
    selected_item = table.selection()
    if len(selected_item) == 1:
        values = table.item(selected_item, 'values')
        pdf_name = values[0]
        max_pages = selected_files[pdf_name]['End Page']
        dialog = CustomPagesDialog(app, pdf_name, max_pages)
        new_custom_pages = dialog.result
        
        if new_custom_pages is not None:
            customization = parse_input(new_custom_pages)
            if len(customization) != len(set(customization)): # there are dups
                customization = list(set(customization))
            if is_valid_page_range(customization, pdf_name):
                selected_files[pdf_name]['Customized'] = customization
                table.item(selected_item, values=(pdf_name, new_custom_pages))

def parse_input(input_text: str) -> list:
    if not input_text: return []
    parts = input_text.split(',')
    if not parts: return []
    pages = []
    
    for part in parts:
        if '-' in part:
            start, end = part.split('-')
            try:
                start_page = int(start)
                end_page = int(end)
                if start_page >= 0 and end_page >= 0:
                    pages.extend(range(start_page, end_page + 1))
            except ValueError as e:
                pass
        else:
            try:
                page = int(part)
                if page >= 0:
                    pages.append(page)
            except ValueError as e:
                pass
    pages.sort()
    return pages

def is_valid_page_range(selected_pages: list, pdf_name:str) -> bool:
    max_page = selected_files[pdf_name]["End Page"]
    return all(1 <= page <= max_page for page in selected_pages)

def validate_merged_file_name(merged_pdf_name: str) -> bool:
    pattern = r'(.*?)\.(pdf)$'
    return match(pattern, merged_pdf_name) is not None

def merge_pdfs():

    if len(selected_files) < 1:
        messagebox.showerror("Invalid", "There must be at least 1 pdf files!")
        return
    
    name = merged_name_entry.get().strip()
    if not name:
        messagebox.showerror("Invalid", "Please specify name of merged file")
        return
    
    if not validate_merged_file_name(name):
        messagebox.showwarning("Invalid merged PDF name", "Please use only letters, digits, spaces, hyphens, and underscores follwed by '.pdf'")
        return
    
    pdf_writer = PdfFileWriter()

    for key, value in selected_files.items():
        pdf_path = value["Full Path"]
        customized_pages = value["Customized"]
        input_pdf = PdfFileReader(open(pdf_path, "rb"))
        if not customized_pages:
            # If the list of pages to extract is empty, extract all pages
            for page in range(len(input_pdf.pages)):
                pdf_writer.addPage(input_pdf.pages[page])
        else:
            for page in customized_pages:
                if page == 0: page = 0
                else: page = page - 1
                pdf_writer.addPage(input_pdf.pages[page])

    # Save the extracted pages to the output file
    with open(name, "wb") as output:
        pdf_writer.write(output)
    
    messagebox.showinfo("Success", f"All pdf merged! Files located in {os.path.abspath(name)}")
    table.delete(*table.get_children())
    selected_files.clear()
    merged_name_entry.delete(0, END)


if '__main__' == __name__:
    app = Tk()
    app.geometry("950x500")
    # app.state("zoomed")
    app.title("PDF Merge Tool")

    select_files_button = Button(app, text="Select PDF", command=select_file)
    select_files_button.pack()

    delete_selected_button = Button(app, text="Delete Selection", command=delete_selected)
    delete_selected_button.pack(side="top", padx=5, pady=5)
    
    columns = ("PDF Name", "Custom Pages")
    table = ttk.Treeview(app, columns=columns, show="headings")

    for col in columns:
        table.heading(col, text=col)
        table.column(col, width=450)

    table.column("Custom Pages", anchor="center")
    table.pack()
    table.bind("<Double-1>", edit_custom_pages)

    merged_name_label = Label(app, text="Merged PDF Name:")
    merged_name_label.pack()
    merged_name_entry = Entry(app)
    merged_name_entry.pack()

    Button(app, text="Merge", command=merge_pdfs).pack()

    quit_frame = Frame(app)
    quit_frame.pack(side="bottom", padx=10, pady=10, anchor="se")
    Button(quit_frame, text="Quit", command=app.quit).pack()

    app.mainloop()
