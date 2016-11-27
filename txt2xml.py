# coding: utf-8

import os
import re

rxWords = re.compile('^([^\\w0-9’ʼ]*)(.+?)([^\\w0-9’ʼ]*)$')


def process_alignment(lines):
    lines = re.sub(' *\t *— *([\t\n])', ' —\\1', lines)
    lines = [l for l in lines.split('\n') if len(l) > 2]
    if len(lines) % 2 != 0:
        print('********\nOdd number of lines in the alignment:', lines)
        return ''
    result = ''
    sourceLines = lines[::2]
    glossLines = lines[1::2]
    for i in range(len(sourceLines)):
        wordsSource = [w.strip() for w in sourceLines[i].split('\t')
                       if len(w.strip()) > 0]
        wordsGloss = [w.strip() for w in glossLines[i].split('\t')
                      if len(w.strip()) > 0]
        if len(wordsGloss) != len(wordsSource):
            print('********\nBroken alignment.\nSource: ' + sourceLines[i] +
                  '\nGloss: ' + glossLines[i])
            continue
        for j in range(len(wordsSource)):
            m = rxWords.search(wordsSource[j])
            if m is None:
                print('********\nWrong word: ' + wordsSource[j])
                continue
            if len(m.group(1)) > 0:
                result += '<word><item type="punct" lang="source-lang">' +\
                          m.group(1) + '</item></word>\n'
            result += '<word><item type="txt" lang="source-lang">' +\
                      m.group(2) + '</item><item type="gls" lang="ru">' +\
                      wordsGloss[j] + '</item></word>\n'
            if len(m.group(3)) > 0:
                result += '<word><item type="punct" lang="source-lang">' +\
                          m.group(3) + '</item></word>\n'
    return result


def my_convert2xml(text):
    '''tekes a text, returns xml and meta'''
    print('\n\n==========\n' + text.strip().split('\n', 1)[0] + '\n\n==========\n')
    text = text.split('@')
    gloss, trans = text[0], text[1]
    meta = gloss.split('\n\n', 1)[0].replace('\n', '\t')
    gloss = re.findall('(?<=\n\n)\t?([0-9]+?)\.\n(.+?)\n\n', gloss, flags = re.DOTALL)
    trans = re.findall('[\n ]([0-9]+?)\.(.+?)(?=[ \n][0-9$])', trans, flags = re.DOTALL)
    gloss_dict = {sentence[0] : [sentence[1]] for sentence in gloss}
    for tr in trans:
        gloss_dict[tr[0]].append(tr[1])
    debugger(gloss_dict)
    gloss_dict = [tuple([num, gloss_dict[num]]) for num in gloss_dict]
    gloss_dict = sorted(gloss_dict,  key=lambda x: int(x[0]))
    result = convert_and_join(gloss_dict)
    return result, meta


def convert_and_join(gloss_dict):
    result = '<interlinear-text>\n<paragraph>\n<phrases>\n'
    for line in gloss_dict:
        result += '<word><words>\n'
        result += process_alignment(line[1][0])
        result += '</words>\n'
        result += '<item type="segnum" lang="en">' + line[0] + '</item>\n'
        result += '<item type="gls" lang="ru">' + line[1][1].strip() + '</item>\n'
        result += '</word>\n'
    result += '</phrases>\n</paragraph>\n</interlinear-text>'
    return result


def debugger(inpt):
    # print(trans[1][0] + ' | ' + trans[1][1])
    with open('/tmp/lookhere', 'w') as f:
        for line in inpt:
            # f.write(str(line))
            f.write(line + ' : ' + str(inpt[line]) + '\n')

    for key in inpt:
        if len(inpt[key]) < 2:
            print('***\nGlosses are not matched with translation:\n')
            print(inpt[key][0])
            print('***\n')


def process_file(fname):
    print('\n\n=================\nStarting ' + fname + '...')
    fIn = open(fname, 'r', encoding='utf-8-sig')
    fileText = fIn.read().replace('¬', '')
    fIn.close()
    texts = fileText.split('#')
    xmlTexts = [my_convert2xml(t) for t in texts if len(t) > 20]
    xmlOutput = '\n'.join(t[0] for t in xmlTexts)
    csvOutput = '\n'.join(str(i + 1) + '\t' + xmlTexts[i][1]
                          for i in range(len(xmlTexts)))
    fnameXml = fname + '-out.xml'
    fXml = open(fnameXml, 'w', encoding='utf-8-sig')
    fXml.write('<?xml version="1.0" encoding="utf-8"?>\n'
               '<document xsi:noNamespaceSchemaLocation="file:FlexInterlinear.xsd" '
               'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">\n')
    fXml.write(xmlOutput)
    fXml.write('\n</document>')
    fXml.close()
    fnameCsv = fname + '-meta.csv'
    fCsv = open(fnameCsv, 'w', encoding='utf-8-sig')
    fCsv.write(csvOutput)
    fCsv.close()


def txt2txt(fname):
    fIn = open(fname, 'r', encoding='utf-8-sig')
    fileText = fIn.read().replace('¬', '')
    fIn.close()
    texts = fileText.split('#')
    new_text = ''
    for text in texts:
        print('\n\n==========\n' + text.strip().split('\n', 1)[0] + '\n\n==========\n')
        text = text.split('@')
        gloss, trans = text[0], text[1]
        new_text += gloss.split('\n\n', 1)[0] + '\n\n'
        gloss = re.findall('(?<=\n\n)\t?([0-9]+?)\.\n(.+?)\n\n', gloss, flags = re.DOTALL)
        trans = re.findall('[\n ]([0-9]+?)\.(.+?)(?=[ \n][0-9$])', trans, flags = re.DOTALL)
        gloss_dict = {sentence[0] : [sentence[1]] for sentence in gloss}
        for tr in trans:
            gloss_dict[tr[0]].append(tr[1])
        debugger(gloss_dict)
        gloss_dict = [tuple([num, gloss_dict[num]]) for num in gloss_dict]
        gloss_dict = sorted(gloss_dict,  key=lambda x: int(x[0]))
        new_text = write2txt(gloss_dict, new_text) + '------\n\n'
    with open('readable_godoberi.txt', 'w') as f:
        f.write(new_text)

def write2txt(gloss_dict, new_text):
    for sent in gloss_dict:
        new_text += '\n' + sent[0] + '.\n' + '\n'.join(sent[1]) + '\n\n'
    return new_text



def process_dir(dirname):
    for root, dirs, files in os.walk(dirname):
        for fname in files:
            if not fname.lower().endswith('.txt'):
                continue
            # process_file(fname)
            txt2txt(fname)


if __name__ == '__main__':
    process_dir('.')
