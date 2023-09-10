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


def isSubjectLessRelation(subject, root, verbRelation, entities, subTreeEntities, mo):
    return subject is None and se.isModifier(root) \
           and len(verbRelation) == 0 and len(entities) == 1 and (len(subTreeEntities) > 0 or len(mo) > 0)

def hasSubjectConflict(mainSubject, foundSubject):
    if mainSubject is None:
        if foundSubject is None:
            return True
    elif foundSubject is not None:
        return mainSubject != foundSubject

    return False


def getImportantChildren(token):
    subject = None
    entities = []
    subTreeEntries = []
    cj = []
    mo = []
    cjMo = []
    numbers = []
    numberMo = []

    for child in token.children:
        if se.isNumber(child):
            numbers.append(child)
        elif se.isValidEntity(child):
            if se.isSubject(child):
                if subject is not None:
                    if not se.isPronoun(child):
                        subject = child
                else:
                    subject = child
            elif not se.isConjunct(child):
                entities.append(child)
        elif se.isVerb(child) and (se.isClausalObject(child) or se.isPredicate(child) \
                                   or se.isPrepositionalObject(child) or child.dep_ == 'cvc'):
            subTreeEntries.append(child)
        elif se.isAdverb(child) and se.isPredicate(child) and token.lemma_ == 'sein':
            subTreeEntries.append(child)
        elif se.isConjunct(child) and not se.isConjunct(token) and se.isVerb(child):
            cj += [child] + se.getConjuncts(child, child.pos_)
        elif se.isAndOr(child):
            for grandchild in child.children:
                if se.isPreposition(grandchild):
                    cjMo.append(grandchild)

            cj += se.getConjuncts(child, child.head.pos_)
        elif se.isValidModifier(child) or se.isPassiveSubject(child) or se.isPrepositionalObject(child) or child.dep_ == 'cvc':
            if se.hasNumberChild(child):
                numberMo.append(child)
            else:
                mo.append(child)

    if len(entities) <= 0:
        entities += numbers
    if len(mo) <= 0:
        mo += numberMo

    return subject, entities, subTreeEntries, cj, mo, cjMo


def getRelationsFromVerbs(subRoots, verbRelation=[], objects=[], mainSubject=None):
    relations = []
    for root in subRoots:
        subject, entities, subTreeEntries, cj, mo, cjMo = getImportantChildren(root)

        if isSubjectLessRelation(subject, root, verbRelation, entities, subTreeEntries, mo):
            subject = entities[0]
            entities = []

        if hasSubjectConflict(mainSubject, subject):
            if len(objects) > 0 and len(verbRelation) > 0:
                subjectConjunctions = [mainSubject] + se.getConjuncts(mainSubject, mainSubject.pos_)
                for entity in objects:
                    objectConjunctions = [entity] + se.getConjuncts(entity, entity.pos_)

                    relations += combineConjunctionsAsRelations(subjectConjunctions, verbRelation, objectConjunctions)
            continue

        if se.isConjunct(root):
            if subject is None and len(entities) == 0 and len(subTreeEntries) == 0 and len(mo) == 0:
                entities = objects
            else:
                entities += objects

                origin = se.getConjunctionOrigin(root)

                entities = [entity for entity in entities if entity not in origin.children]
        else:
            entities += objects

        if mainSubject is not None:
            subject = mainSubject
        verbPath = verbRelation + [root]

        if len(subTreeEntries) > 0:
            relations += getRelationsFromVerbs(subTreeEntries, verbPath, entities, subject)
        elif len(entities) > 0:
            subjectConjunctions = [subject] + se.getConjuncts(subject, subject.pos_)
            for entity in entities:
                objectConjunctions = [entity] + se.getConjuncts(entity, entity.pos_)

                relations += combineConjunctionsAsRelations(subjectConjunctions, verbPath, objectConjunctions)
        elif len(mo) > 0:
            relations += getRelationsFromVerbs(mo, verbPath, entities, subject)

        if len(cj) > 0:
            if se.hasPreposition(cj) and not se.isValidModifier(verbPath[-1]):
                relations += getRelationsFromVerbs(cj, verbPath, [], subject)
            else:
                relations += getRelationsFromVerbs(cj, verbPath[:-1], entities, subject)

        if len(cjMo) > 0:
            relations += getRelationsFromVerbs(cjMo, verbPath, [], subject)

    return relations

def getRelationsFromConjunctVerbs(conjunctVerbs):
    relations = []

    for verb in conjunctVerbs:
        subject, entities, subTreeEntries, cj, mo, cjMo = getImportantChildren(verb)

        if subject is None:
            continue

        if len(entities) > 0:
            subjectConjunctions = [subject] + se.getConjuncts(subject, subject.pos_)
            for entity in entities:
                objectConjunctions = [entity] + se.getConjuncts(entity, entity.pos_)

                relations += combineConjunctionsAsRelations(subjectConjunctions, [verb], objectConjunctions)
        elif len(subTreeEntries) > 0:
            relations += getRelationsFromVerbs(subTreeEntries, [verb], mainSubject=subject)
        elif len(mo) > 0:
            relations += getRelationsFromVerbs(mo, [verb], mainSubject=subject)
        elif len(cj) > 0:
            if se.hasPreposition(cj):
                relations += getRelationsFromVerbs(cj, [verb], entities, subject)

    return relations


def extractVerbRelations(doc):
    relations = []

    verbs = []
    conjunctVerbs = []
    for token in doc:
        if se.isVerb(token):
            if se.isConjunct(token):
                conjunctVerbs.append(token)
            else:
                verbs.append(token)

    relations += getRelationsFromVerbs(verbs)
    relations += getRelationsFromConjunctVerbs(conjunctVerbs)

    return relations


def getVerbPath(sb, root):
    tmpRoot = root
    verbPath = [tmpRoot]
    subTreeRoot = None

    while True:
        subject, entities, subTreeEntries, cj, mo, cjMo = getImportantChildren(tmpRoot)
        if len(subTreeEntries) > 0:
            tmpRoot = subTreeEntries[0]
        elif len(mo) > 0:
            tmpRoot = mo[0]
        else:
            if len(entities) > 0:
                verbPath.clear()
                break

            verbChildren = se.getVerbChildren(verbPath[-1])
            if len(verbChildren) == 1:
                subTreeRoot = verbChildren[0]
            break

        if subject is not None and subject != sb:
            subTreeRoot = verbPath[-1]
            verbPath.pop()
            break

        if len(entities) > 0:
            verbPath.clear()
            break

        verbPath.append(tmpRoot)

    return verbPath, subTreeRoot

def getBackgroundRelations(subjects):
    relations = []

    for sb in subjects:
        root = sb.head
        verbPath, subTreeRoot = getVerbPath(sb, root)

        if len(verbPath) <= 0 or subTreeRoot is None:
            continue

        for child in subTreeRoot.children:
            if se.isSentenceConjunction(child) and not se.isConditionToken(child):
                verbPath.append(child)

        conjunctions = [sb] + se.getConjuncts(sb, sb.pos_)
        relations.append([conjunctions, verbPath, [subTreeRoot]])

    return relations

def extractBackgroundRelations(doc):
    subjects = []

    for token in doc:
        if se.isSubject(token):
            subjects.append(token)

    return getBackgroundRelations(subjects)
