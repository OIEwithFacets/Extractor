import spacy
import os
import argparse

import SpacyEssentials as se
import VerbRelationExtractor as ve
import NounRelationExtractor as ne
import FacetExtractor as fe
import Combiner as cmb

def isFlawedTree(doc):
    for sentence in doc.sents:
        if se.isVerb(sentence.root):
            return False

    return True

def shiftModifierToEntity(relation):
    if not se.isVerb(relation[1][-1]) and (se.isModifier(relation[1][-1]) or se.isPreposition(relation[1][-1])):
        relation[2].insert(0, relation[1][-1])
        relation[1] = relation[1][:-1]


def getNounsAsString(nouns, root):
    output = ''
    for noun in nouns:
        if not se.isNoun(noun) and not se.isPronoun(noun) and not se.isNumber(noun):
            output += se.getNounString(noun, root) + ' '
        else:
            output += se.getNounString(noun, root) + ', '

    return output[:-2]

def getVerbsAsString(verbs):
    output = ''
    for verb in verbs:
        for child in verb.children:
            if se.isVerbPart(child) or se.isAdditionalZu(child) or se.isSich(child):
                output += child.text + ' '
            elif se.isValidModifier(child):
                for grandchild in child.children:
                    if se.isSich(grandchild):
                        output += child.text + ' ' + grandchild.text + ' '
                        break

        output += verb.text + ' '

    return output[:-1]

def facetToString(facet):
    if len(facet) <= 0:
        return '[]'
    output = ''
    for part in facet:
        if se.isNoun(part):
            output += se.getNounString(part, None) + ' '
        else:
            output += part.text + ' '
    return output[:-1]

def printFacets(facets, file, tab, isCondition=False, doc=None):
    if len(facets) <= 0:
        file.write(tab + '[]\n')
        return

    if isCondition:
        if len(facets) <= 0:
            file.write(tab + '[]\n')
            return
        file.write(tab + se.getBackgroundSubTree(facets[0], doc) + '\n')
        return

    for facet in facets:
        file.write(tab + facetToString(facet[0]) + '\n')
        if tab == 'sb: ' or tab == 'vb: ' or tab == 'ob: ':
            if facet[1] is not None:
                printFacets(facet[1], file, '\t\t')
            tab = '\t'
        else:
            if facet[1] is not None:
                printFacets(facet[1], file, tab + '\t')

def printResult(file, sentId, relation, facets, customString='', doc=None):
    root = relation[0][0].head

    output = sentId + '\t'

    output += getNounsAsString(relation[0], root) + '\t'

    if len(customString) > 0 and customString != 'backGround':
        output += customString + '\t'
    else:
        output += getVerbsAsString(relation[1]) + '\t'

    if doc is not None and customString == 'backGround':
        output += se.getBackgroundSubTree(relation[2][0], doc)
    else:
        output += getNounsAsString(relation[2], root)

    file.write(output + '\n')

    printFacets(facets[0], file, 'sb: ')
    printFacets(facets[1], file, 'vb: ')
    printFacets(facets[2], file, 'ob: ')
    printFacets(facets[3], file, 'cd: ', isCondition=True, doc=doc)


def processVerbRelations(verbRelations, doc, id, outputFileFacets, outputFileCombined):
    for relation in verbRelations:
        shiftModifierToEntity(relation)

        facets = fe.searchForFacets(relation)
        printResult(outputFileFacets, str(id), relation, facets, doc=doc)

        print(relation)
        print('sb:', facets[0])
        print('vb:', facets[1])
        print('ob:', facets[2])
        if len(facets[3]) > 0:
            print('cd:', se.getBackgroundSubTree(facets[3][0], doc))
        else:
            print('cd: []')
        combinations = cmb.combineRelationWithFacets(relation, facets)
        for combination in combinations:
            outputFileCombined.write(str(id) + '\t' + combination + '\n')
            print(combination)

def processIstRelations(istRelations, id, outputFileFacets, outputFileCombined):
    for relation in istRelations:
        facets = fe.searchForFacets(relation, isCustomMade=True)
        printResult(outputFileFacets, str(id), relation, facets, customString='*ist*')

        print('[' + str(relation[0]) + ' *ist* ' + str(relation[2]) + ']')
        print('sb:', facets[0])
        print('vb:', facets[1])
        print('ob:', facets[2])
        print('cd: []')

        combinations = cmb.combineRelationWithFacets(relation, facets, True, '*ist*')
        for combination in combinations:
            outputFileCombined.write(str(id) + '\t' + combination + '\n')
            print(combination)

def processHatRelations(hatRelations, id, outputFileFacets, outputFileCombined):
    for relation in hatRelations:
        facets = fe.searchForFacets(relation, isCustomMade=True)
        printResult(outputFileFacets, str(id), relation, facets, customString='*hat*')

        print('[' + str(relation[0]) + ' *hat* ' + str(relation[2]) + ']')
        print('sb:', facets[0])
        print('vb:', facets[1])
        print('ob:', facets[2])
        print('cd: []')

        combinations = cmb.combineRelationWithFacets(relation, facets, True, '*hat*')
        for combination in combinations:
            outputFileCombined.write(str(id) + '\t' + combination + '\n')
            print(combination)

def processPrepositionRelations(prepRelations, id, outputFileFacets, outputFileCombined):
    for relation in prepRelations:
        facets = fe.searchForFacets(relation, isCustomMade=True)
        printResult(outputFileFacets, str(id), relation, facets)

        print(relation)
        print('sb:', facets[0])
        print('vb:', facets[1])
        print('ob:', facets[2])
        print('cd: []')

        combinations = cmb.combineRelationWithFacets(relation, facets, True, relation[1][0].text)
        for combination in combinations:
            outputFileCombined.write(str(id) + '\t' + combination + '\n')
            print(combination)

def processBackgroundRelations(backgroundRelations, doc, id, outputFileFacets, outputFileCombined):
    for relation in backgroundRelations:
        facets = fe.searchForFacets(relation, isBackground=True)
        printResult(outputFileFacets, str(id), relation, facets, customString='backGround', doc=doc)

        print(relation)
        print('sb:', facets[0])
        print('vb:', facets[1])
        print('ob: []')
        print('cd: []')

        combinations = cmb.combineRelationWithFacets(relation, facets, doc=doc)
        for combination in combinations:
            outputFileCombined.write(str(id) + '\t' + combination + '\n')
            print(combination)

def processSplitRelations(splitRelations, id, outputFileFacets, outputFileCombined):
    for relation in splitRelations:
        outputFileFacets.write(str(id) + '\t' + relation + '\n')
        outputFileFacets.write('sb: []\n')
        outputFileFacets.write('vb: []\n')
        outputFileFacets.write('ob: []\n')
        outputFileFacets.write('cd: []\n')

        print(relation)
        print('sb: []')
        print('vb: []')
        print('ob: []')
        print('cd: []')

        outputFileCombined.write(str(id) + '\t' + relation + '\n')


def main(transformer, inputFile, outputFileFacets, outputFileCombined):
    nlp = spacy.load(transformer)
    print('Loaded model!')

    i = 1

    for line in inputFile.readlines():
        if i < 0:
            i += 1
            continue

        sentence = line.replace('\n', '')

        doc = nlp(sentence)

        if isFlawedTree(doc):
            print(str(i), 'ERROR!\n')
            i += 1
            continue

        verbRelations = ve.extractVerbRelations(doc)
        backgroundRelations = ve.extractBackgroundRelations(doc)

        istRelations, hatRelations, prepRelations, splitRelations = ne.extractNounRelations(doc)

        print(str(i), sentence)

        processVerbRelations(verbRelations, doc, i, outputFileFacets, outputFileCombined)

        processIstRelations(istRelations, i, outputFileFacets, outputFileCombined)

        processHatRelations(hatRelations, i, outputFileFacets, outputFileCombined)

        processPrepositionRelations(prepRelations, i, outputFileFacets, outputFileCombined)

        processBackgroundRelations(backgroundRelations, doc, i, outputFileFacets, outputFileCombined)

        processSplitRelations(splitRelations, i, outputFileFacets, outputFileCombined)

        print('')
        i += 1

    inputFile.close()
    outputFileFacets.close()
    outputFileCombined.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Usage of the extractor',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('src', help='input file')
    parser.add_argument('--dest', default=os.getcwd(), help='folder for the results')
    parser.add_argument('--model', default='de_dep_news_trf', help='spaCy model')

    args = parser.parse_args()
    config = vars(args)

    inputPath = config['src']
    outputPath = config['dest']
    spacyTransformer = config['model']

    inputFile = open(inputPath, 'r', encoding='utf-8')
    outputFileFacets = open(os.path.join(outputPath, 'extractedTuplesWithFacets.txt'), 'w', encoding='utf-8')
    outputFileCombined = open(os.path.join(outputPath, 'extractedTuples.txt'), 'w', encoding='utf-8')

    main(spacyTransformer, inputFile, outputFileFacets, outputFileCombined)
