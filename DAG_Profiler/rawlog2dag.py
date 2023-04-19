import json
import sys

# Check if the required arguments are provided
if len(sys.argv) != 3:
    print("Usage: python rawlog2dag.py <input_file> <output_file>")
    sys.exit(1)

# Get the input and output file names from the command-line arguments
input_file = sys.argv[1]
output_file = sys.argv[2]

# Read JSON data from the input file
with open(input_file, 'r') as json_file:
    json_data = json.load(json_file)

# Create a dictionary to map the JSON keys to the custom keys

output = []
esindex = 0
deindex = 0
# Convert the JSON data to the custom data format
for i in range(len(json_data['E2E'])):
    resnet = int(json_data['resnet'][i][0])
    langdetect = int(json_data['langdetect'][i][0])
    e2e = int(json_data['E2E'][i][0])
    
    if esindex >= len(json_data['es2en']):
        lang2en = int(json_data['de2en'][deindex][0])
        deindex += 1
    else:
        if deindex >= len(json_data['de2en']):
            lang2en = int(json_data['es2en'][esindex][0])
            esindex += 1
        else:
            # Pick es2en or de2en based on which brings sum closer to E2E
            if abs(e2e - (resnet + langdetect + int(json_data['es2en'][esindex][0]))) < abs(e2e - (resnet + langdetect + int(json_data['de2en'][deindex][0]))):
                lang2en = int(json_data['es2en'][esindex][0])
                esindex += 1
            else:
                lang2en = int(json_data['de2en'][deindex][0])
                deindex += 1
    
    output.append(' '.join([f"resnet:{resnet}", f"langdetect:{langdetect}", f"lang2en:{lang2en}", f"E2E:{e2e}"]) + '\n')


# Write the custom data format to the output file
with open(output_file, 'w') as output_file:
    output_file.writelines(output)
