import spacy

def isRoot(token):
    return token.dep_ == 'ROOT'

def isSubject(token):
    return token.dep_ == 'sb'

def isPassiveSubject(token):
    return token.dep_ == 'sbp'

def isObject(token):
    return token.dep_ == 'oa' or token.dep_ == 'oc' or token.dep_ == 'og' or token.dep_ == 'op'

def isVerb(token):
    return token.pos_ == 'VERB' or token.pos_ == 'AUX'

def isAdjective(token):
    return token.pos_ == 'ADJ'

def isAdverb(token):
    return token.pos_ == 'ADV'

def isSepVerbPrefix(token):
    return token.dep_ == 'svp'

def isFiniteVerb(token):
    return isVerb(token) and token.tag_.endswith('FIN')

def isNoun(token):
    return token.pos_ == 'NOUN' or token.pos_ == 'PROPN'

def isNormalNoun(token):
    return token.tag_ == 'NN'

def isNegate(token):
    return token.dep_ == 'ng'

def isNamedEntity(token):
    return token.tag_ == 'NE'

def isPronoun(token):
    return token.pos_ == 'PRON'

def isNonReflexivePronoun(token):
    return token.tag_ == 'PPER'

def isSubstitute(token):
    return token is not None and (token.tag_ == 'PDS' or token.tag_ == 'PIS' or token.tag_ == 'PPOSS' or token.tag_ == 'PRELS' or token.tag_ == 'PWS' or token.tag_ == 'PRF' or token.tag_ == 'PPER')

def isConjunct(token):
    return token.dep_ == 'cj'

def isApposition(token):
    return token.dep_ == 'app'

def isModifier(token):
    return token.dep_ == 'mo'

def isClausalObject(token):
    return token.dep_ == 'oc'

def isPostModifier(token):
    return token.dep_ == 'mnr'

def isPrepositionalObject(token):
    return token.dep_ == 'op'

def isParenthetic(token):
    return token.dep_ == 'par'

def isGenitiveAttribute(token):
    return token.dep_ == 'ag'

def isNounKernel(token):
    return token.dep_ == 'nk'

def isPreposition(token):
    return token.tag_ == 'APPR' or token.tag_ == 'APPRART'

def isPWAV(token):
    return token.tag_ == 'PWAV'

def isKOUI(token):
    return token.tag_ == 'KOUI'

def isKOUS(token):
    return token.tag_ == 'KOUS'

def isCompound(token):
    return token.dep_ == 'pnc'

def isVerbPart(token):
    return token.tag_ == 'PTKVZ'

def isAdditionalZu(token):
    return token.tag_ == 'PTKZU'

def isSich(token):
    return token.text == 'sich'

def isPredicate(token):
    return token.dep_ == 'pd'

def isNumber(token):
    return token.tag_ == 'CARD'

def isArticle(token):
    return token.tag_ == 'ART'

def isDeterminer(token):
    return token.pos_ == 'DET'

def isPronominalAdverb(token):
    return token.tag_ == 'PROAV'

def isExpletiveEs(token):
    return token.dep_ == 'ep'

def isWordRemnant(token):
    return token.tag_ == 'TRUNC' or token.text[-1] == '-'

def isAndOr(token):
    return token.dep_ == 'cd'

def isRelativeClause(token):
    return token.dep_ == 'rc'

def isAttributePronoun(token):
    return token.tag_ in ['PDAT', 'PIAT', 'PPOSAT', 'PRELAT', 'PWAT']

def isPossessivePronoun(token):
    return token.tag_ == 'PPOSAT' or token.tag_ == 'PPOSS'


def getConjuncts(token, pos):
    conjuncts = []
    posHelper = []
    if isAndOr(token):
        posHelper = [token.head.pos_]

    if pos == 'AUX' or pos == 'VERB':
        posHelper = ['AUX', 'VERB']
    elif pos == 'PROPN' or pos == 'NOUN' or pos == 'PRON':
        posHelper = ['PROPN', 'NOUN', 'PRON']

    for child in token.children:
        if isConjunct(child) and (child.pos_ == pos or child.pos_ in posHelper or isWordRemnant(child)):
            conjuncts += [child]+getConjuncts(child, pos)
        if isAndOr(child):
            conjuncts += getConjuncts(child, pos)

    return conjuncts

def getConjunctionOrigin(token):
    if not isConjunct(token):
        return token

    head = token.head
    andOrCounter = 0
    while isConjunct(head) or isAndOr(head):
        if isAndOr(head.head) and andOrCounter > 0:
            return head
        else:
            andOrCounter += 1

        head = head.head

    return head

def searchFirstNounChild(token):
    for child in token.children:
        if isNoun(child):
            return child
    return None

def getSubjectChild(token):
    for child in token.children:
        if isSubject(child):
            return child
    return None

def getConjunctionSubstitute(substitute, root):
    tmp = root.head
    sb = getSubjectChild(tmp)
    while sb is None:
        tmp = tmp.head
        sb = getSubjectChild(tmp)
        if isRoot(tmp) and sb is None:
            return substitute

    if isNoun(sb):
        return sb

    return substitute

def replaceSubstitute(substitute, root):
    origin = getConjunctionOrigin(root)

    if isRelativeClause(origin) and isNoun(origin.head):
        return origin.head

    if substitute.tag_ == 'PIS':
        replacement = searchFirstNounChild(substitute)
        if replacement is not None:
            return replacement

    if isConjunct(root):
        mo = None
        if isModifier(substitute.head):
            mo = substitute.head

        if isSubject(substitute):
            for child in origin.children:
                if isSubject(child):
                    return child
        else:
            for child in origin.children:
                if mo is not None:
                    if mo == child:
                        for grandchild in child.children:
                            if isNoun(grandchild):
                                return grandchild
                elif not isSubject(child) and isNoun(child):
                    return child
    return substitute


def getNounCompounds(token, useLemma):
    name = ''
    for left in token.lefts:
        if left.dep_ == 'pnc':
            name += getNounCompounds(left, useLemma)+' '

    if useLemma:
        name += token.lemma_
    else:
        name += token.text

    for right in token.rights:
        if right.dep_ == 'pnc':
            name += ' '+getNounCompounds(right, useLemma)

    return name

def getBackgroundSubTree(rootToken, doc):
    if len(rootToken) <= 0:
        return '[]'

    lowestIndex = len(doc)
    highestIndex = 0

    for token in rootToken.subtree:
        index = token.i
        if index < lowestIndex:
            lowestIndex = index
        elif index > highestIndex:
            highestIndex = index

    txt = ''
    for j in range(lowestIndex, highestIndex+1):
        if isSentenceConjunction(doc[j]) and doc[j].head == rootToken:
            continue

        if doc[j].dep_ == 'punct':
            txt += doc[j].text
        else:
            txt += ' ' + doc[j].text

    if txt[0] == ' ':
        return txt[1:]
    return txt

def isSentenceConjunction(token):
    return token.tag_ == 'KOUS' or token.tag_ == 'KOKOM'

def isConditionToken(token):
    return isSentenceConjunction(token) and token.text.lower() in ['wenn', 'falls', 'sofern']


def getNounString(token, root):
    if isSubstitute(token) and root is not None:
        return getNounString(replaceSubstitute(token, root), None)
    if isPronoun(token):
        return token.text
    if isNormalNoun(token):
        return getNounCompounds(token, False)
    return getNounCompounds(token, False)


def isValidAdverb(token):
    return isAdverb(token) and not isSepVerbPrefix(token) and not isPronominalAdverb(token)

def isValidNoun(token):
    return isNoun(token) and (not isModifier(token) or isNamedEntity(token))

def isValidPronoun(token):
    return isPronoun(token) and not isExpletiveEs(token) and token.text not in ['mehr', 'sich']

def isValidEntity(token):
    return isValidNoun(token) or isValidPronoun(token)

def isValidModifier(token):
    return isModifier(token) and not isVerb(token)

def isDetailFacet(token, isCustomMade):
    return isAdjective(token) or isNumber(token) or isNegate(token) or isValidAdverb(token) \
           or ((isPronoun(token) or isAttributePronoun(token) or isArticle(token)) and not isCustomMade and not isSubstitute(token))


def hasNumberChild(token):
    for child in token.children:
        if isNumber(child):
            return True
    return False

def getVerbChildren(token):
    verbs = []
    for child in token.children:
        if isVerb(child):
            verbs.append(child)
    return verbs

def hasPreposition(tokens):
    for token in tokens:
        if isPreposition(token):
            return True
    return False
