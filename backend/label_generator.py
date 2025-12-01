"""
Label Generator Module
Adapted from participant_code_generator_advanced.py
"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.graphics.barcode import code128, qr
from reportlab.graphics import renderPDF
from reportlab.graphics.shapes import Drawing


# Common label format presets
LABEL_FORMATS = {
    'avery5160': {
        'name': 'Avery 5160 (30 labels)',
        'label_width': 2.625 * inch,
        'label_height': 1 * inch,
        'labels_per_row': 3,
        'labels_per_column': 10,
        'left_margin': 0.1875 * inch,
        'top_margin': 0.5 * inch,
        'horizontal_gap': 0.125 * inch,
        'vertical_gap': 0
    },
    'avery5161': {
        'name': 'Avery 5161 (20 labels)',
        'label_width': 4 * inch,
        'label_height': 1 * inch,
        'labels_per_row': 2,
        'labels_per_column': 10,
        'left_margin': 0.15625 * inch,
        'top_margin': 0.5 * inch,
        'horizontal_gap': 0.1875 * inch,
        'vertical_gap': 0
    },
    'avery5163': {
        'name': 'Avery 5163 (10 labels)',
        'label_width': 4 * inch,
        'label_height': 2 * inch,
        'labels_per_row': 2,
        'labels_per_column': 5,
        'left_margin': 0.15625 * inch,
        'top_margin': 0.5 * inch,
        'horizontal_gap': 0.1875 * inch,
        'vertical_gap': 0
    }
}


class AdvancedLabelGenerator:
    """Advanced label generator with customization options."""

    def __init__(self, start_code, end_code, code_type='barcode',
                 label_format='avery5160', prefix='', suffix=''):
        """
        Initialize the generator.

        Args:
            start_code (int): Starting code
            end_code (int): Ending code
            code_type (str): 'barcode' or 'qrcode'
            label_format (str): Label format preset name
            prefix (str): Prefix for participant codes
            suffix (str): Suffix for participant codes
        """
        self.start_code = start_code
        self.end_code = end_code
        self.code_type = code_type.lower()
        self.prefix = prefix
        self.suffix = suffix

        # Load label format
        if label_format in LABEL_FORMATS:
            format_spec = LABEL_FORMATS[label_format]
            self.label_width = format_spec['label_width']
            self.label_height = format_spec['label_height']
            self.labels_per_row = format_spec['labels_per_row']
            self.labels_per_column = format_spec['labels_per_column']
            self.left_margin = format_spec['left_margin']
            self.top_margin = format_spec['top_margin']
            self.horizontal_gap = format_spec['horizontal_gap']
            self.vertical_gap = format_spec['vertical_gap']
            self.format_name = format_spec['name']
        else:
            raise ValueError(f"Unknown label format: {label_format}")

    def format_code(self, code_value):
        """Format code with prefix and suffix."""
        return f"{self.prefix}{code_value}{self.suffix}"

    def generate_qrcode(self, code_value, size):
        """Generate a QR code."""
        formatted_code = self.format_code(code_value)
        qr_code = qr.QrCodeWidget(formatted_code)
        bounds = qr_code.getBounds()
        width = bounds[2] - bounds[0]
        height = bounds[3] - bounds[1]
        drawing = Drawing(size, size, transform=[
                          size/width, 0, 0, size/height, 0, 0])
        drawing.add(qr_code)
        return drawing

    def draw_label(self, c, x, y, code_value):
        """Draw a single label."""
        formatted_code = self.format_code(code_value)

        # Add text
        c.setFont("Helvetica-Bold", 9)
        text_x = x + self.label_width / 2
        text_y = y + self.label_height - 0.15 * inch

        c.drawCentredString(text_x, text_y, f"ID: {formatted_code}")

        # Add barcode or QR code
        if self.code_type == 'qrcode':
            qr_size = min(self.label_width * 0.7, self.label_height * 0.7)
            qr_x = x + (self.label_width - qr_size) / 2
            qr_y = y + 0.1 * inch
            qr_drawing = self.generate_qrcode(code_value, qr_size)
            renderPDF.draw(qr_drawing, c, qr_x, qr_y)
        else:  # barcode
            barcode_width = self.label_width - 0.2 * inch
            barcode_height = self.label_height * 0.5
            barcode_x = x + (self.label_width - barcode_width) / 2
            barcode_y = y + 0.2 * inch

            # Create barcode
            barcode = code128.Code128(
                formatted_code, barHeight=barcode_height * 0.8, barWidth=0.9)
            barcode.drawOn(c, barcode_x, barcode_y)

    def generate_pdf(self, output_filename, page_size=letter):
        """Generate the PDF file."""
        c = canvas.Canvas(output_filename, pagesize=page_size)
        page_width, page_height = page_size

        codes = range(self.start_code, self.end_code + 1)
        label_count = 0

        for code in codes:
            row = (label_count % (self.labels_per_row *
                   self.labels_per_column)) // self.labels_per_row
            col = label_count % self.labels_per_row

            x = self.left_margin + col * \
                (self.label_width + self.horizontal_gap)
            y = page_height - self.top_margin - \
                (row + 1) * self.label_height - row * self.vertical_gap

            self.draw_label(c, x, y, code)

            label_count += 1

            if label_count % (self.labels_per_row * self.labels_per_column) == 0:
                c.showPage()

        c.save()

        total_pages = (len(codes) - 1) // (self.labels_per_row *
                                           self.labels_per_column) + 1
        return len(codes), total_pages
