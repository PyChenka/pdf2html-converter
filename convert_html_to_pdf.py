import pdfkit


def convert_html_to_pdf(html_path, output_pdf_directory, css_path):
    file_name = html_path.split('/')[-1].split('.')[0]
    output_pdf_path = output_pdf_directory + file_name + '.pdf'
    footer_html = 'footer.html'

    config = pdfkit.configuration(
        wkhtmltopdf='../../Program Files/wkhtmltopdf/bin/wkhtmltopdf.exe')
    options = {
        'page-size': 'A4',
        'margin-top': '0.75in',
        'margin-right': '0.75in',
        'margin-bottom': '0.75in',
        'margin-left': '0.75in',
        'encoding': "UTF-8",
        'custom-header': [
            ('Accept-Encoding', 'gzip')
        ],
        'no-outline': None,
        'footer-html': footer_html
    }

    pdfkit.from_file(html_path, output_pdf_path, configuration=config, options=options, css=css_path)
    
    print("PDF file created successfully.")


# Пути к файлам
html_path = 'Result HTML/Federal_Decree_Law_№_32_of_2021_regarding_trading_companies.html'
output_pdf_directory = 'Result PDF/'
css_path = 'ar_style.css'

convert_html_to_pdf(html_path, output_pdf_directory, css_path)

# Federal Law № 2 of 1971 Concerning the Union Flag
# Federal_Decree_Law_№_32_of_2021_regarding_trading_companies
# Federal_Law_№_10_of_1972_Concerning_the_emblem_of_the_United_Arab
# Federal_Law_№_47_of_2022_in_the_matter_of_corporate_and_business
# Ministerial_Resolution_№_71_of_1989_Regarding_the_procedures_for
# Resolution_of_the_Supreme_Council_of_the_Federation_№_3_of_1996
