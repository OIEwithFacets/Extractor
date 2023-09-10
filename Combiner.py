import SpacyEssentials as se


def sortTokens(elements, root):
    def swap(i, j):
        elements[i], elements[j] = elements[j], elements[i]

    replacement = None
    value = 0
    for e in elements:
        if se.isSubstitute(e):
            replacement = se.replaceSubstitute(e, root)
            value = e.i - replacement.i
        if replacement == e:
            replacement = None
            value = 0

    n = len(elements)
    swapped = True
    x = -1

    while swapped:
        swapped = False
        x += 1

        for i in range(1, n-x):
            x = 0
            y = 0
            if se.getConjunctionOrigin(elements[i-1]).head == replacement:
                x = value
            if se.getConjunctionOrigin(elements[i]).head == replacement:
                y = value

            if elements[i-1].i + x > elements[i].i + y:
                swap(i-1, i)
                swapped = True

    return elements

def getFacetsOfFacet(facetChunks):
    elements = []
    if facetChunks is None:
        return elements

    for chunk in facetChunks:
        facet = chunk[0]
        facetsOfFacet = chunk[1]

        elements += facet
        elements += getFacetsOfFacet(facetsOfFacet)

    return elements


def combineSubjectFacets(nouns, facetChunks, root):
    elements = nouns

    if facetChunks is not None:
        for chunk in facetChunks:
            facet = chunk[0]
            facetsOfFacet = chunk[1]

            elements += facet
            elements += getFacetsOfFacet(facetsOfFacet)

    sortedTokens = sortTokens(elements, root)

    output = ''
    for token in sortedTokens:
        if se.isValidEntity(token) or se.isSubstitute(token):
            output += ' ' + se.getNounString(token, root)
        else:
            output += ' ' + token.text

    return output[1:]

def combineVerbFacets(verbs, facetChunks, root):
    elements = verbs

    for verb in verbs:
        for child in verb.children:
            if se.isVerbPart(child) or se.isAdditionalZu(child) or se.isSich(child):
                elements.append(child)
            elif se.isValidModifier(child):
                for grandchild in child.children:
                    if se.isSich(grandchild):
                        elements.append(child)
                        break

    modifierFacets = []

    if facetChunks is not None:
        for chunk in facetChunks:
            facet = chunk[0]
            facetsOfFacet = chunk[1]

            if len(facet) == 1 and se.isDetailFacet(facet[0], False):
                elements += facet
                elements += getFacetsOfFacet(facetsOfFacet)
            else:
                modifierFacets.append(chunk)

    sortedTokens = sortTokens(elements, root)

    output = ''
    for token in sortedTokens:
        if se.isNoun(token) or se.isSubstitute(token):
            output += ' ' + se.getNounString(token, root)
        else:
            output += ' ' + token.text

    return output[1:], modifierFacets

def getObjectElementsFromFacets(oldObject, facetChunks):
    result = []
    for chunk in facetChunks:
        facet = chunk[0]
        facetsOfFacet = chunk[1]

        elements = facet

        modifierFacets = []
        if facetsOfFacet is not None:
            for fofChunk in facetsOfFacet:
                fofFacet = fofChunk[0]
                fofFacetsOfFacet = fofChunk[1]

                if len(fofFacet) == 1 and se.isDetailFacet(fofFacet[0], False):
                    elements += fofFacet
                    elements += getFacetsOfFacet(fofFacetsOfFacet)
                else:
                    modifierFacets.append(fofChunk)

        result.append([oldObject, elements])
        if len(modifierFacets) > 0:
            result += getObjectElementsFromFacets(oldObject + elements, modifierFacets)

    return result

def combineObjectFacets(objects, facetChunks, root):
    results = []
    if len(objects) <= 0:
        return results

    elements = objects

    modifierFacets = []
    if facetChunks is not None:
        for chunk in facetChunks:
            facet = chunk[0]
            facetsOfFacet = chunk[1]

            if len(facet) == 1 and se.isDetailFacet(facet[0], False):
                elements += facet
                elements += getFacetsOfFacet(facetsOfFacet)
            else:
                modifierFacets.append(chunk)

    objectElements = [[[], elements]]
    objectElements += getObjectElementsFromFacets(elements, modifierFacets)

    for part in objectElements:
        output = ''
        preTab = part[0]
        posTab = part[1]

        sortedTokens = sortTokens(preTab, root)
        for token in sortedTokens:
            if se.isNoun(token) or se.isSubstitute(token):
                output += ' ' + se.getNounString(token, root)
            else:
                output += ' ' + token.text

        output += '\t'
        sortedTokens = sortTokens(posTab, root)
        for token in sortedTokens:
            if se.isNoun(token) or se.isSubstitute(token):
                output += se.getNounString(token, root) + ' '
            else:
                output += token.text + ' '

        results.append(output[:-1])

    return results


def combineRelationWithFacets(relation, facets, isCustomMade=False, phrase='', doc=None):
    result = []

    sb = relation[0]
    vb = relation[1]
    ob = relation[2]

    root = sb[0].head

    sbFacets = facets[0]
    vbFacets = facets[1]
    obFacets = facets[2]

    subjectPhrase = combineSubjectFacets(sb, sbFacets, root)

    verbPhrase, vbModifierFacets = combineVerbFacets(vb, vbFacets, root)

    if doc is not None:
        subTree = se.getBackgroundSubTree(relation[2][0], doc)

        result.append(subjectPhrase + '\t' + verbPhrase + '\t' + subTree)

        for facetChunk in vbModifierFacets:
            facet = facetChunk[0]
            facetsOfFacet = facetChunk[1]

            vbStrings = combineObjectFacets(facet, facetsOfFacet, root)

            for vbPhrase in vbStrings:
                result.append(subjectPhrase + '\t' + verbPhrase + ' ' + vbPhrase.replace('\t', '') + '\t' + subTree)

        return result

    if isCustomMade:
        verbPhrase = phrase

    obStrings = combineObjectFacets(ob, obFacets, root)

    for objectPhrase in obStrings:
        result.append(subjectPhrase + '\t' + verbPhrase + objectPhrase)
        for facetChunk in vbModifierFacets:
            facet = facetChunk[0]
            facetsOfFacet = facetChunk[1]

            vbStrings = combineObjectFacets(facet, facetsOfFacet, root)

            for vbPhrase in vbStrings:
                result.append(subjectPhrase + '\t' + verbPhrase + objectPhrase.replace('\t', ' ') + vbPhrase)

    return result
