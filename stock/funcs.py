import pyexcel


def get_records_as_list_with_dicts(file_type, content, header, excel_header_fields):
    records = pyexcel.get_records(file_type=file_type, file_content=content)
    records_list = []
    excel_header_fields = [field.lower() for field in excel_header_fields]
    for record in records:
        row = {}
        for header_field in header:
            if header_field.lower() in excel_header_fields:
                row[header_field] = record[header_field]
            print(f"{header_field} --- {excel_header_fields}")
        records_list.append(row)
    #print(f"AKHI: {records_list}")
    return records_list


def check_excel_for_duplicates(excel_list):
    duplicates = []
    excel_index = 2

    for row in excel_list:
        row_occurences = 0

        for next_row in excel_list:
            #print(f"AKHI: {row}")
            if "block" in row["lagerplatz"].lower():
                continue

            if next_row == row:
                row_occurences += 1
            if row_occurences == 2:
                duplicates.append((row, excel_index))
                print(duplicates)
                break
        excel_index += 1
    return duplicates