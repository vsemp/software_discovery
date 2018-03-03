# -*- coding: utf-8 -*-
"""
Created by Vladimir Pchelin on 10/28/17.

Copyright © 2017 Vladimir Pchelin. All rights reserved.
"""

import yaml
import os
import random
from random import randint

GLOBAL_LOG = ''

def get_label_to_tokens(filename):
    """
    Returns the corpus: a dictionary from labels to sets of tokens.
    """
    label_to_tokens = dict()
    with open(filename, encoding='utf8') as f:
        content = f.readlines()
    for line in content:
        line = line[:-1]
        if line[:4] == '==> ' and line[-4:] == ' <==':
            label = line[4:-4]
        else:
            if label not in label_to_tokens:
                label_to_tokens[label] = set()
            label_to_tokens[label].add(line)
    return label_to_tokens


def get_token_to_labels(label_to_tokens):
    """
    Returns the inverse map: a dictionary from tokens to sets of labels.
    """
    token_to_labels = dict()
    for label in label_to_tokens:
        for token in label_to_tokens[label]:
            if token not in token_to_labels:
                token_to_labels[token] = set()
            token_to_labels[token].add(label)
    return token_to_labels


def get_label_to_token_groups(token_to_labels):
    """
    Returns a categorized corpus. It's a dictionary from labels to groups
    of tokens. These groups are indexed with natural numbers. Index of a
    group shows in how many labels each token from this group is present.
    """
    label_to_token_groups = dict()
    for token in token_to_labels:
        for label in token_to_labels[token]:
            index = len(token_to_labels[token])
            if label not in label_to_token_groups:
                label_to_token_groups[label] = dict()
            if index not in label_to_token_groups[label]:
                label_to_token_groups[label][index] = set()
            label_to_token_groups[label][index].add(token)
    return label_to_token_groups
  
     
def get_duplicates(label_to_tokens, token_to_labels, label_to_token_groups):
    """
    Returns labels, not all, that have sets of tokens identical to other labels.
    From each group of identical labels one label goes to representatives. 
    All the other labels from each group go to <duplicates>.
    """
    duplicates = set()
    for label in sorted(label_to_tokens.keys()):
        if label in duplicates:
            continue
        first_index = sorted(label_to_token_groups[label].keys())[0]
        first_token = list(label_to_token_groups[label][first_index])[0]
        potential_duplicates = token_to_labels[first_token]
        for other_label in sorted(list(potential_duplicates)):
            if (other_label <= label) or (other_label in duplicates):
                continue
            if label_to_tokens[label] == label_to_tokens[other_label]:
                duplicates.add(other_label)
                print('Duplicates: {0} = {1}'.format(label, other_label))
    return duplicates
  
       
def get_rules_per_label(label, label_to_tokens, token_to_labels,
                        label_to_token_groups, limit = 1, max_index = 0):
    """
    Generates rules, at most <limit>, for a specified <label>.
    
    Each rule is a list of <index> triplets.
    
    Each rules includes exactly one triplet
    of the format:
        (*) (<token>, 'unique to', <index>)
    It means that <token> appears exactly in <index> different labels including
    <label>. All these labels, except <label>, are listed exactly once in other
    triplets as <other_label>. A triplet of this format always goes first.
    
    Other triplets have the formats:
        (1) (<token>, 'inside vs', <other_label>) or
        (2) (<token>, 'outside vs', <other_label>)
    It means that <token> distinguishes <label> from <other_label>. Format (1)
    means that <token> is in <label> but not in <other_label>. Format (2) means
    that <token> is in <other_label> but not in <label>.
    
    Rules are ordered in a list according to <index>. There could be less rules
    than <limit>. Across all rules each token can appear only once in a triplet
    of format (*) and only once in a triplet of format (1) or (2). This
    guarantees that changes to one token will affect at most two rules. It's
    also guaranteed that rules have the smallest possible <indeces> under the
    requirement given above.
    """
    assert (label in label_to_token_groups)
    rules = []
    used_tokens = set()
    for index in sorted(label_to_token_groups[label].keys()):
        if index > max_index and max_index > 0:
            break
        for token in label_to_token_groups[label][index]:
            if token in used_tokens:
                continue
            rule = []
            rule.append((token, 'unique to', str(index)))
            for other_label in token_to_labels[token]:
                if other_label == label:
                    continue
                plus_diff = label_to_tokens[label] - label_to_tokens[other_label]
                minus_diff = label_to_tokens[other_label] - label_to_tokens[label]
                assert (len(plus_diff) + len(minus_diff)) > 0
                plus_diff -= used_tokens
                minus_diff -= used_tokens
                if len(plus_diff) > 0:
                    rule.append((list(plus_diff)[0], 'inside vs', other_label))
                elif len(minus_diff) > 0:
                    rule.append((list(minus_diff)[0], 'outside vs', other_label))
                else:
                    break
            if len(rule) < index:
                continue
            rules.append(rule)
            for triplet in rule:
                used_tokens.add(triplet[0])
            if len(rules) >= limit:
                return rules
    return rules

               
def get_rules(label_to_tokens, token_to_labels, label_to_token_groups,
              limit = 1, max_index = 5):
    """
    Generates a dictionary from labels to sets of rules.
    
    See description of <get_rules_per_label> for more details.
    """
    rules = dict()
    for label in label_to_token_groups:
        rules[label] = get_rules_per_label(label, label_to_tokens,
             token_to_labels, label_to_token_groups, limit, max_index)
    return rules

#
# Test on Anthony's data
#
def read_anthony_data(dirname, union = False, rate = 1, threshold = 1000):
    """
    Read in data provided by Anthony.

    By default only 'union' files are used!!!
    """
    counter = dict()
    anthony_data = dict()
    filenames = os.listdir(dirname)
    for filename in filenames:
        filename_label = filename.split('.')[0]
        if (filename_label in counter) and (counter[filename_label] > threshold):
            continue
        if randint(0, 999)/1000.0 > rate:
            continue
        if 'yaml' not in filename:
            continue
        if union and 'union' not in filename: # By default only 'union' files are used
            continue
        if (not union) and 'union' in filename:
            continue
        
        with open(os.path.join(dirname, filename), encoding='utf8') as f:
            filedata = yaml.load(f)
        if 'label' not in filedata:
            print(str(os.path.join(dirname, filename)) + " missed label !!!!")
            continue
        label = filedata['label']
        #label = ''.join([l for l in label if l.isalpha()])
        changes = set(filedata['changes'])
        for c in changes:
            c = c[4:]
        if label not in anthony_data:
            anthony_data[label] = dict()
        anthony_data[label][filename] = changes
        if label not in counter:
            counter[label] = 0
        counter[label] += 1
    return anthony_data

def read_anthony_data_testing(dirname):
    """
    Read in data provided by Anthony.

    By default only 'union' files are used!!!
    """
    anthony_data = dict()
    filenames = os.listdir(dirname)
    for filename in filenames:

        with open(os.path.join(dirname, filename), encoding='utf8') as f:
            filedata = yaml.load(f)
        changes = set(filedata['changes'])
        for c in changes:
            c = c[4:]
        true_labels = filedata['labels']
        anthony_data[filename] = (changes, true_labels)
    return anthony_data

def transform_anthony_intersection(data):
    res = dict()
    for label in data:
        for filename in data[label]:
            if label not in res:
                res[label] = dict()
            for token in data[label][filename]:
                if token not in res[label]:
                    res[label][token] = 1
                else:
                    res[label][token] += 1
            #res[label] = res[label].intersection(data[label][filename])
    newres = dict()
    for label in res:
        newres[label] = set()
        maxval = max(res[label].values())
        for token in sorted(res[label], key=res[label].get, reverse=True):
            if res[label][token] != maxval and len(newres[label]) > 50:
                break
            if res[label][token] < 0.94 * maxval and len(newres[label]) >= 40:
                break
            if res[label][token] < 0.88 * maxval and len(newres[label]) >= 26:
                break
            if res[label][token] < 0.8 * maxval and len(newres[label]) >= 16:
                break
            if res[label][token] < 0.7 * maxval and len(newres[label]) >= 10:
                break
            if res[label][token] < 0.6 * maxval and len(newres[label]) >= 8:
                break
            if res[label][token] < 0.5 * maxval and len(newres[label]) >= 6:
                break
            newres[label].add(token)
    return newres

def transform_anthony_data(data):
    res = dict()
    for k, v in data.items():
        kk = list(v.keys())[0]
        res[k] = set(v[kk])
    return res
        
def if_label(label_tested, label_rules, true_labels, filename, changes, threshold):
    success = 0
    global GLOBAL_LOG
    num_rules = len(label_rules)
    for rule in label_rules:
        correct_rule = True
        for triplet in rule:
            token = triplet[0]
            inside = (triplet[1] != 'outside vs')
            if inside == (len([v for v in changes if token == v[-len(token):]]) == 0):
                if label_tested in true_labels:
                    to_print = 'A rule broke on triplet: {0} {1} {2} filename: {3}'.format(triplet[0], triplet[1], triplet[2], filename)
                    print(to_print)
                    GLOBAL_LOG += to_print + '\n'
                correct_rule = False
                break
        if correct_rule:
            if label_tested not in true_labels:
                to_print = 'Identified {0} as {1} where the rule has triplet: {2} {3} {4}'.format(filename, label_tested, rule[0][0], rule[0][1], rule[0][2])
                print(to_print)
                GLOBAL_LOG += to_print + '\n'
            success += 1
    return (success / num_rules) >= threshold
    

def check_rules_on_anthony_data(rules, anthony_data, threshold = 1):
    """
    If it doesn't print anything this means everything is good.
    """
    labels = rules.keys()
    res_matrix = dict()
    parameters = dict()
    parameters['threshold'] = threshold
    parameters['num_rules'] = dict()
    num_rules = 0
    for label in labels:
        parameters['num_rules'][label] = len(rules[label])
        num_rules += len(rules[label])
    parameters['avg_num_rules'] = num_rules / len(labels)
    
    for filename, pair in anthony_data.items():
        changes = pair[0]
        true_labels = pair[1]
        predicted_labels = []
        for label_tested in labels:
            label_rules = rules[label_tested]
            if len(label_rules) == 0:
                print('There are no rules for label {0}'.format(label_tested))
                exit()
            if if_label(label_tested, label_rules, true_labels, filename, changes, threshold):
                predicted_labels.append(label_tested)
        res_matrix[filename] = predicted_labels
    
    return (res_matrix, parameters)
 
def save_results(res_matrix, parameters, dirname, filename):
    #df = pd.DataFrame(res_matrix)
    #df.to_csv(os.path.join(dirname, filename + "_table.cvs"))
    with open(os.path.join(dirname, filename + "_table.yaml"), encoding='utf8', mode ='w') as f:
        yaml.dump(res_matrix, f)
    with open(os.path.join(dirname, filename + "_parameters.yaml"), encoding='utf8', mode ='w') as f:
        yaml.dump(parameters, f)
    with open(os.path.join(dirname, filename + "_logs.txt"), encoding='utf8', mode ='w') as f:
        global GLOBAL_LOG
        f.write(GLOBAL_LOG)
        GLOBAL_LOG = ''
  
             
#
# Generate rules from the corpus
#
# Get label to tokens corpus from a file (apt or yum / paths or tuples or names)
#label_to_tokens = get_label_to_tokens(r'C:\Users\20176817\Documents\CloudArticle\vladimir\vladimir\apt\tuples')
anthony_corpus = read_anthony_data(r'C:\Users\20176817\Documents\CloudArticle\yaml\training', union = False)
label_to_tokens = transform_anthony_intersection(anthony_corpus)
# Filter out labels given by yum that refer to i686 architecture
label_to_tokens = {k: v for k, v in label_to_tokens.items() if k[-5:] != '.i686'
                   and 'glibc' not in k and 'apache2' not in k} 
# Get the inverse map
token_to_labels = get_token_to_labels(label_to_tokens)
# Get the map from labels to categorized tokens
label_to_token_groups = get_label_to_token_groups(token_to_labels)
# Find duplicates
duplicates = get_duplicates(label_to_tokens, token_to_labels, label_to_token_groups)
# Filter out duplicates from the corpus
label_to_tokens = {k: v for k, v in label_to_tokens.items() if k not in duplicates} 
# Again get the inverse map
token_to_labels = get_token_to_labels(label_to_tokens)
# Again get the map from labels to categorized tokens
label_to_token_groups = get_label_to_token_groups(token_to_labels)
# Generate rules for all labels      
rules = get_rules(label_to_tokens, token_to_labels, label_to_token_groups, limit = 1)
# Free memory
#del duplicates
#del label_to_token_groups
#del token_to_labels
#del label_to_tokens

param_list = [0.5]#, 0.025, 0.075, 0.125, 0.175, 0.225, 0.275, 0.325, 0.375, 0.425, 0.475, 0.575, \
              #0.675, 0.775, 0.875, 0.975]
source_list = ['3-apps', '4-apps', '5-apps']

for param in param_list:
    for source in source_list:
        # Read Anthony's data
        anthony_data = read_anthony_data_testing(r'C:\Users\20176817\Documents\CloudArticle\yaml\{0}'.format(source))
        # Filter out rules for labels that are not in Anthony's data
        #rules = {k: v for k, v in rules.items() if k in anthony_data.keys()}
        # Check the rule on data. If nothing is printed it's good.
        
        #for thres in param_list:
        res_matrix, parameters = check_rules_on_anthony_data(rules, anthony_data, threshold = param)
        
        parameters['testing_set'] = source
        save_results(res_matrix, parameters, r'C:\Users\20176817\Documents\CloudArticle\results',
                     filename = parameters['testing_set'] + '_' + str(round(parameters['avg_num_rules']))  + '_' + str(parameters['threshold']))

#import json
#dirname = r'C:\Users\20176817\Documents\CloudArticle\results'
#filename = parameters['training_set'] + '_' + str(round(parameters['avg_num_rules']))  + '_' + str(parameters['threshold'])
#with open(os.path.join(dirname, filename + "_rules.json"), encoding='utf8', mode ='w') as f:
#    json.dump(rules, f, indent=0, separators=(',', ':'))

############ tools
def preproc_stats(label_to_token_groups):
    res = dict()
    res2 = dict()
    for l in label_to_token_groups:
        res[l] = min( list( label_to_token_groups[l].keys() ) )
    for l in res:
        if res[l] not in res2:
            res2[res[l]] = 0
        res2[res[l]] += 1
    return res2

def num_occur(label_to_tokens):
    res = 0
    for l in label_to_tokens:
        res += len(label_to_tokens[l])
    return res

#pre_stats = preproc_stats(label_to_token_groups)
#n_occur = num_occur(label_to_tokens)

def read_results(dirname, filtr):
    res = dict()
    filenames = os.listdir(dirname)
    for filename in filenames:
        if filtr not in filename:
            continue
        if 'table' not in filename:
            continue
        avr_rules = int(filename.split('_')[1])
        if int(avr_rules) == 1:
            continue
        thres = float(filename.split('_')[2])
        with open(os.path.join(dirname, filename), encoding='utf8') as f:
            filedata = yaml.load(f)
        res[thres] = filedata['total']['f1-score']
    return res

#graph_res = read_results(r'C:\Users\20176817\Documents\CloudArticle\vladimir_all_results\results_RP', filtr='anthony')
        