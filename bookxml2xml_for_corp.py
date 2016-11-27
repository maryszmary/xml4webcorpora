# coding: utf-8

import os
import re
import lxml.etree
import time
import xml.sax.saxutils

rxWords = re.compile('^([^\\w0-9’ʼ]*)(.+?)([^\\w0-9’́̀ʼ]*)$')

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


def convert2xml(text):
    result = '<interlinear-text>\n'
    meta, start_of_text = get_meta(text)
    title = meta.split('\t')[0]
    result += '<item type="title" lang="en">' + title + '</item>\n'
    result += '<paragraphs>\n<paragraph>\n<phrases>\n'
    body = get_text(text, start_of_text)
    print('1:\n' +meta)
    if body is not None:
        for sentence in body:
            sentNo, lines, trans, footnotes = sentence[0], sentence[1], sentence[2], sentence[3]
            result += '<word><words>\n'
            result += process_alignment(lines)
            result += '</words>\n'
            result += '<item type="segnum" lang="en">' + sentNo.strip() + '</item>\n'
            result += '<item type="gls" lang="en">' + xml.sax.saxutils.escape(trans.strip()) + '</item>\n'
            for fn in footnotes:
                result += '<item type="note" lang="en">' + xml.sax.saxutils.escape(fn.strip()) + '</item>\n'
            result += '</word>\n'
        result += '</phrases>\n</paragraph>\n</paragraphs>\n</interlinear-text>'
        return result, meta
    print('body is none')

def get_text(text, start):
    '''получает экземпляры узлов с отдельными текстами, возвращает список кортежей с глоссами и переводом'''
    paragraphs = text.xpath('para')[start:]
    gloss_lines, smthn_weird = get_sentences([el for el in paragraphs if el.text is not None and '\t' in el.text])
    translations, comments = get_sentences([el for el in paragraphs if el.text is not None and '\t' not in el.text])
    gl = convert_to_strings(footnote_dealer(gloss_lines))
    tr = convert_to_strings(footnote_dealer(translations))
    if len(gl) != len(tr):
        pass
        for a in set([el[0] for el in gl]).difference(set([el[0] for el in tr])):
            print(a)
    else:
        return [[tr[i][0], gl[i][1], tr[i][1], tr[i][2] + gl[i][2]] for i in range(len(gl))]



def translations_spliter(paragraphs):
    '''получает 3-х-мерный массив из convert_to_strings с текстами предложений, 
    возвращает такое же, но с правильно разделёнными предложениями, правильно сопоставленными им сносками
    и отделёнными номерами'''
    translations = []
    for group in paragraphs:
        # '(\\([0-9]+[аб]?\\)|[IXV]+\\.)(.+?)(?=\n[IXV]+\\.|\\([0-9]+[аб]?\\)|$)' 
        # есть ли у нас римскиие цифры и боимся ли мы I.sg
        cur_translations = re.findall('([0-9]+[аб]?\\.)(.+?)(?=\n[0-9]+[аб]?\\.|$)',
            group[0], flags = re.DOTALL)
        translations += [[el[0], el[1], []] for el in cur_translations]

        if group[1] != []:
            for footnote in group[1]:
                for sent in range(len(translations)):
                    if '[[[footnote-mark]]]' in translations[sent][1]:
                        translations[sent][2].append(footnote)
                        translations[sent][1] = translations[sent][1][:translations[sent][1].index('[[[')] +\
                                                translations[sent][1][translations[sent][1].index('[[[') + 19:]
                        break
    return translations


def convert_to_strings(sentences, split_sentences = False):
    '''получает 3-х-мерный массив из footnote_dealer с объектами тегов, возвращает такой же массив,
    но с текстами предложений, причём предложения разделены правильно'''
    text_sentences = [['\n'.join([line.text for line in group[0]]),
                       [line.text for line in group[1]]] for group in sentences]
    text_sentences = translations_spliter(text_sentences)
    return text_sentences


def footnote_dealer(sentences):
    '''получает список тегов с предложениями, возвращает массив массивов, в каждом из которых два элемента: 
    массив с тегами предложений и массив с тегами сносок'''
    new_sentences = []
    for i in range(len(sentences)):
        new_sentences.append([sentences[i], []])
        for line in sentences[i]:
            for fn in line.xpath('footnote/para'):
                fn.text = re.split('[\s\t]', line.text)[-1] + ': ' + fn.text # эта строка значит, что в каждой сноске пишется предыдущее слово
                new_sentences[-1][1] += [fn]
                fn.getparent().getparent().text += '[[[footnote-mark]]]'
                if fn.getparent().tail:
                    fn.getparent().getparent().text += fn.getparent().tail

    # for arr in new_sentences:
    #     for sent in arr[0]:
    #         print(sent.text)
    #     for sent in arr[1]:
    #         print('FOOTNOTES: \n' + sent.text)        
    return new_sentences

def get_sentences(paragraphs):
    '''получает список со всеми тегами, не относящимися к заглавию текста, возвращает
    массив массивов, каждый из которых прядставляет из себя предложение, где каждый элемент массива -- тег с одной строкой'''
    sentences, comments = [], []
    for el in paragraphs:
        if el.text[0] in '(IXV0123456789':
            sentences.append([el])
        else:
            try:
                sentences[len(sentences) - 1] += [el]
            except IndexError:
                comments.append([el])
    # for el in sentences:
    #     print('\nnumber of lines: ' + str(len(el)))
    #     for i in el:
    #         print(i.text)
    # time.sleep(20)
    return sentences, comments

def get_meta(text):
    '''получает экземпляры узлов с отдельными текстами, возвращает метаданные и элемент, с которого начинается текст'''
    meta = [text.xpath('title')[0].text]
    info = text.xpath('para')[:6]
    for el in range(len(info)):
        if info[el].text is None:
            start_of_text = el + 1
            break
        else:
            meta.append(info[el].text)
    meta = '\t'.join(meta)
    return meta, start_of_text


def process_file(fname):
    print('\n\n=================\nStarting ' + fname + '...')
    fIn = open(fname, 'r', encoding='utf-8-sig')
    file_text = fIn.read().replace('¬', '')
    fIn.close()

    texts = lxml.etree.fromstring(file_text).xpath('sect1')
    print('number of texts: ' + str(len(texts)))

    xmlTexts = [convert2xml(t) for t in texts if len(t) > 20]
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


def process_dir(dirname):
    for     fname in os.listdir(dirname):
        if not fname.lower().endswith('.xml') or fname.lower().endswith('-out.xml'):
            continue
        process_file(fname)


if __name__ == '__main__':
    process_dir('.')
    