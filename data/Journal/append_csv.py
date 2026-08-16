import csv
import sys
import json

def append_to_csv(csv_path, json_path):
    with open(json_path, 'r', encoding='utf-8') as jf:
        data = json.load(jf)
    with open(csv_path, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        for row in data:
            writer.writerow([row.get('Date', ''), row.get('Gratitude', ''), row.get('Plan', ''), row.get('Tasks', ''), row.get('Review', ''), row.get('Takeaway', '')])

if __name__ == '__main__':
    csv_path = sys.argv[1]
    json_path = sys.argv[2]
    append_to_csv(csv_path, json_path)
