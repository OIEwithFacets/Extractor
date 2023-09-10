import SpacyEssentials as se


def getFacetsFromFacet(token, isCustomMade):
    facets = []

    for child in token.children:
        if se.isConjunct(child) or child.dep_ == 'pnc':
            continue

        if se.isDetailFacet(child, isCustomMade) or se.isGenitiveAttribute(child) \
                or (se.isNoun(child) and not se.isCompound(child)):
            conjunctions = [child] + se.getConjuncts(child, child.pos_)
            for cj in conjunctions:
                facets.append([[cj], getFacetsFromFacet(cj, isCustomMade)])
        elif se.isValidModifier(child) or se.isPreposition(child):
            for grandchild in child.children:
                if se.isValidEntity(grandchild):
                    conjunctions = [grandchild] + se.getConjuncts(grandchild, grandchild.pos_)
                    for cj in conjunctions:
                        facets.append([[child, cj], getFacetsFromFacet(cj, isCustomMade)])

    if len(facets) > 0:
        return facets

    return None


def getNounFacets(noun, sb, ob, isCustomMade):
    facets = []

    sbOrigin = se.getConjunctionOrigin(sb)
    obOrigin = se.getConjunctionOrigin(ob)
    for child in noun.children:
        if child == sb or se.isConjunct(child) or child.dep_ == 'pnc' or se.isSich(child):
            continue

        if se.isDetailFacet(child, isCustomMade) or (se.isGenitiveAttribute(child) and not isCustomMade):
            conjunctions = [child] + se.getConjuncts(child, child.pos_)
            for cj in conjunctions:
                facets.append([[cj], getFacetsFromFacet(cj, isCustomMade)])
        elif (se.isValidModifier(child) or se.isPreposition(child)) and not isCustomMade:
            for grandchild in child.children:
                if grandchild == sb:
                    continue

                if se.isValidEntity(grandchild):
                    origin = se.getConjunctionOrigin(grandchild)
                    if origin == sbOrigin or origin == obOrigin:
                        continue

                    conjunctions = [grandchild] + se.getConjuncts(grandchild, grandchild.pos_)
                    for cj in conjunctions:
                        if cj == ob:
                            continue

                        facets.append([[child, cj], getFacetsFromFacet(cj, isCustomMade)])
    return facets

def getVerbFacets(verbs, sb, ob):
    facets = []
    sbOrigin = se.getConjunctionOrigin(sb)
    obOrigin = se.getConjunctionOrigin(ob)

    i = 0
    for verb in verbs:
        if se.isConjunct(verb):
            break
        i += 1
    if len(verbs) == i:
        i = 0

    for verb in verbs[i:]:
        if not se.isVerb(verb) and not se.isAdverb(verb) and not se.isConjunct(verb):
            continue

        for child in verb.children:
            if child in verbs or se.isConjunct(child) or child == sbOrigin or child == obOrigin or se.isSich(child):
                continue

            if se.isDetailFacet(child, False) or se.isGenitiveAttribute(child) or se.isNounKernel(child):
                conjunctions = [child] + se.getConjuncts(child, child.pos_)
                for cj in conjunctions:
                    facets.append([[cj], getFacetsFromFacet(cj, False)])
            elif se.isValidModifier(child) or se.isPassiveSubject(child) or se.isPreposition(child):
                for grandchild in child.children:
                    if se.isValidEntity(grandchild):
                        if grandchild == sbOrigin or grandchild == obOrigin:
                            continue

                        conjunctions = [grandchild] + se.getConjuncts(grandchild, grandchild.pos_)
                        for cj in conjunctions:
                            facets.append([[child, cj], getFacetsFromFacet(cj, False)])
    return facets

def getConditionalRoots(verbs):
    relationRoots = []
    for verb in verbs:
        for child in verb.children:
            if se.isVerb(child) and child not in verbs:
                for grandchild in child.children:
                    if se.isConditionToken(grandchild):
                        relationRoots.append(child)

    return relationRoots


def searchForFacets(relation, isCustomMade=False, isBackground=False):
    root = relation[0][0].head

    subjectFacets = []
    oldLength = 0
    verbs = relation[1]
    obj = relation[2][0]
    if len(relation[2]) > 1:
        obj = relation[2][1]
    objectFacets = []

    conditionalFacets = []
    if not isCustomMade and not isBackground:
        conditionalFacets = getConditionalRoots(verbs)

    for sb in relation[0]:
        if se.isSubstitute(sb):
            sb = se.replaceSubstitute(sb, root)

        subjectFacets += getNounFacets(sb, relation[0][0], obj, isCustomMade)
        if se.isSubstitute(sb) and len(subjectFacets) <= oldLength:
            subjectFacets += getNounFacets(se.replaceSubstitute(sb, root), relation[0][0], obj, isCustomMade)
        oldLength = len(subjectFacets)

    oldLength = 0
    if not isBackground:
        for ob in relation[2]:
            if se.isSubstitute(ob):
                ob = se.replaceSubstitute(ob, root)

            objectFacets += getNounFacets(ob, relation[0][0], obj, isCustomMade)
            if se.isSubstitute(ob) and len(objectFacets) <= oldLength:
                objectFacets += getNounFacets(se.replaceSubstitute(ob, root), relation[0][0], obj, isCustomMade)
                oldLength = len(objectFacets)

    verbFacets = []
    if not isCustomMade:
        verbFacets += getVerbFacets(verbs, relation[0][0], obj)

    return [subjectFacets, verbFacets, objectFacets, conditionalFacets]
