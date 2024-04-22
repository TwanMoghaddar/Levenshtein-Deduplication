import xml.etree.ElementTree as ET
import re
from difflib import SequenceMatcher
from collections import defaultdict


# Load and parse XML files
def load_xml(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()
    print(f"XML loaded from {file_path}")
    return root


def normalize_string(input_string):
    normalized = re.sub(r'\W+', '', input_string.lower())
    return normalized


def string_similarity(str1, str2):
    norm_str1 = normalize_string(str1)
    norm_str2 = normalize_string(str2)
    matcher = SequenceMatcher(None, norm_str1, norm_str2)
    similarity = matcher.ratio()
    print(f"Comparing '{str1}' to '{str2}', similarity score: {similarity}")
    return similarity


# Extract data from disc elements
def extract_discs_data(xml_root):
    discs_data = []
    for disc in xml_root:
        disc_data = {
            'id': disc.find('id').text if disc.find('id') is not None else "",
            'artist': disc.find('artist').text if disc.find('artist') is not None else "",
            'dtitle': disc.find('dtitle').text if disc.find('dtitle') is not None else ""
        }
        discs_data.append(disc_data)
    print(f"Extracted data for {len(discs_data)} discs")
    return discs_data


# Matching function using artist and title
def match_discs(disc1, disc2, artist_weight=0.5, title_weight=0.5, threshold=0.8):
    artist_similarity_score = string_similarity(disc1['artist'], disc2['artist'])
    title_similarity_score = string_similarity(disc1['dtitle'], disc2['dtitle'])
    total_score = (artist_similarity_score * artist_weight) + (title_similarity_score * title_weight)
    match = total_score >= threshold
    print(
        f"Matching '{disc1['artist']}' - '{disc1['dtitle']}' with '{disc2['artist']}' - '{disc2['dtitle']}', total score: {total_score}, match: {match}")
    return match, total_score


# Create blocks for more efficient matching
def create_blocks(discs_data):
    blocks = defaultdict(list)
    for disc in discs_data:
        key = normalize_string(disc['artist'][:1])
        blocks[key].append(disc)
    print(f"Created {len(blocks)} blocks for matching")
    return blocks


# Find matches within blocks
def find_matches_within_blocks(blocks):
    matches = []
    for key, block in blocks.items():
        for i in range(len(block)):
            for j in range(i + 1, len(block)):
                match, score = match_discs(block[i], block[j])
                if match:
                    matches.append((block[i]['id'], block[j]['id']))
    print(f"Found {len(matches)} matches")
    return matches


# Load ground truth and extract duplicate pairs
def extract_ground_truth_dups(gt_root):
    duplicates = set()
    for pair in gt_root.findall('pair'):
        discs = pair.findall('disc')
        if len(discs) == 2:
            disc1_id = discs[0].find('id').text
            disc2_id = discs[1].find('id').text
            duplicates.add((disc1_id, disc2_id))
            duplicates.add((disc2_id, disc1_id))  # Bidirectional
    print(f"Extracted {len(duplicates)} ground truth duplicates")
    return duplicates


# Calculate precision, recall, and F1-score
def evaluate_matches(matches, ground_truth):
    matches_expanded = set((str(a), str(b)) for a, b in matches)
    matches_expanded.update((str(b), str(a)) for a, b in matches)  # Bidirectional
    ground_truth_expanded = set((str(a), str(b)) for a, b in ground_truth)
    ground_truth_expanded.update((str(b), str(a)) for a, b in ground_truth)  # Bidirectional
    true_positives = len(matches_expanded & ground_truth_expanded)
    precision = true_positives / len(matches_expanded) if matches_expanded else 0
    recall = true_positives / len(ground_truth_expanded) if ground_truth_expanded else 0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) else 0
    print(f"Evaluation results - Precision: {precision}, Recall: {recall}, F1 Score: {f1_score}")
    return precision, recall, f1_score


# Main execution flow
root = load_xml('./DATASOURCES/cddb_discs.xml')
gt_root = load_xml('./DATASOURCES/cddb_9763_dups.xml')
all_discs_data = extract_discs_data(root)
blocks = create_blocks(all_discs_data)
matches = find_matches_within_blocks(blocks)
ground_truth_dups = extract_ground_truth_dups(gt_root)
precision, recall, f1_score = evaluate_matches(matches, ground_truth_dups)
print(f"Final Evaluation - Precision: {precision}, Recall: {recall}, F1 Score: {f1_score}")
