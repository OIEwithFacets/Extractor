import SpacyEssentials as se


def combineConjunctionsAsRelations(subjects, verbPhrase, objects, isCustomMade=False):
    relations = []

    if not isCustomMade:
        if len(objects) > 1 and se.isWordRemnant(objects[1]):
            relations.append([subjects, verbPhrase, objects])
        else:
            for cj in objects:
                relations.append([subjects, verbPhrase, [cj]])

        return relations

    if len(objects) > 1 and se.isWordRemnant(objects[1]):
        if len(subjects) > 1 and se.isWordRemnant(subjects[1]):
            relations.append([subjects, verbPhrase, objects])
        else:
            for cj in subjects:
                relations.append([[cj], verbPhrase, objects])
    else:
        if len(subjects) > 1 and se.isWordRemnant(subjects[1]):
            for cj in objects:
                relations.append([subjects, verbPhrase, [cj]])
        else:
            for cjSubject in subjects:
                for cjObject in objects:
                    relations.append([[cjSubject], verbPhrase, [cjObject]])

    return relations


def extractIstRelations(nouns):
    relations = []

    for noun in nouns:
        if se.isConjunct(noun):
            continue

        parent = noun.head

        if se.isNounKernel(noun) and se.isNamedEntity(noun) and se.isNoun(parent):
            conjunctions = [noun] + se.getConjuncts(noun, noun.pos_)
            for cj in conjunctions:
                relations.append([[cj], [], [parent]])

        if not se.isNoun(parent) and se.isApposition(noun.head):
            grandparent = parent.head
            if se.isNoun(grandparent):
                conjunctionsParent = [grandparent] + se.getConjuncts(grandparent, grandparent.pos_)
                conjunctionsChild = [noun] + se.getConjuncts(noun, noun.pos_)

                relations += combineConjunctionsAsRelations(conjunctionsParent, [], conjunctionsChild, True)

        if se.isGenitiveAttribute(noun) or se.isRoot(noun) or (se.isNamedEntity(noun) and se.isParenthetic(noun)):
            continue

        if len(parent.text) < 2 or len(noun.text) < 2 or not se.isNoun(parent):
            continue

        conjunctionsParent = [parent] + se.getConjuncts(parent, parent.pos_)
        conjunctionsChild = [noun] + se.getConjuncts(noun, noun.pos_)
        if se.isApposition(noun) and not se.isNamedEntity(noun):
            relations += combineConjunctionsAsRelations(conjunctionsParent, [], conjunctionsChild, True)
        elif (se.isNamedEntity(noun) ^ se.isParenthetic(noun)) or noun.dep_ == 'cc':
            relations += combineConjunctionsAsRelations(conjunctionsChild, [], conjunctionsParent, True)

    return relations

def extractHatRelations(nouns):
    relations = []

    for noun in nouns:
        conjuncts = [noun] + se.getConjuncts(noun, noun.pos_)

        if not se.isSubject(noun):
            for child in noun.children:
                if se.isPossessivePronoun(child):
                    if se.isConjunct(noun):
                        if se.isNoun(noun.head):
                            for cj in conjuncts:
                                relations.append([[noun.head], [], [cj]])

                        continue

                    tmp = noun.head
                    sb = se.getSubjectChild(tmp)

                    while sb is None:
                        tmp = tmp.head
                        sb = se.getSubjectChild(tmp)
                        if se.isRoot(tmp) and sb is None:
                            break

                    if sb is None:
                        continue

                    if se.isSubstitute(sb):
                        replacement = se.replaceSubstitute(sb, sb.head)
                        if se.isNoun(replacement):
                            for cj in conjuncts:
                                relations.append([[replacement], [], [cj]])
                    else:
                        for cj in conjuncts:
                            relations.append([[sb], [], [cj]])

        parent = noun.head
        if not se.isNoun(parent):
            continue

        parentConjunctions = [parent] + se.getConjuncts(parent, parent.pos_)

        if se.isGenitiveAttribute(noun):
            relations += combineConjunctionsAsRelations(conjuncts, [], parentConjunctions, True)
        elif se.isNamedEntity(noun) and se.isParenthetic(noun):
            relations += combineConjunctionsAsRelations(conjuncts, [], parentConjunctions, True)

    return relations

def extractPrepRelations(nouns):
    relations = []

    for noun in nouns:
        if se.isPreposition(noun.head) and se.isNoun(noun.head.head):
            conjunctionsChild = [noun] + se.getConjuncts(noun, noun.pos_)
            conjunctionsGrandParent = [noun.head.head] + se.getConjuncts(noun.head.head, noun.head.head.pos_)

            relations += combineConjunctionsAsRelations(conjunctionsGrandParent, [noun.head], conjunctionsChild, True)

    return relations

def extractSplitRelations(nouns):
    relations = []

    for noun in nouns:
        split = noun.text.split('-')
        if len(split) == 2:
            relations.append(split[0] + '\t' + '*hat*' + '\t' + split[1])

    return relations


def extractNounRelations(doc):
    nouns = []

    for token in doc:
        if se.isNoun(token) and not se.isCompound(token) and not se.isModifier(token):
            nouns.append(token)

    istRelations = extractIstRelations(nouns)
    hatRelations = extractHatRelations(nouns)
    prepRelations = extractPrepRelations(nouns)
    splitRelations = extractSplitRelations(nouns)

    return istRelations, hatRelations, prepRelations, splitRelations
