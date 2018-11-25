import argparse
import sys
import math
import numpy
import statistics

class Example:
    """A single piece of data"""
    def __init__(self, attributes, label):
        # [1] is the bias term
        self.attributes = numpy.array([1]+ [int(float(a)) for a in attributes])
        self.label = int(label)

    def __repr__(self):
        return "{0}: {1}".format(self.attributes, self.label)

def loadData(datafile, labelfile):
    data = []
    with open(datafile, "r") as dataF, open(labelfile, "r") as labelF:
        for d, label in zip(dataF, labelF):
            data.append(Example(d.strip().split(" "), label.strip()))

    return data

class DecisionTree:
    def __init__(self, data):
        # on nodes with 0 edges, data is the label
        # on non-leaf nodes, data is the attribute
        self.data = data
        # (value, Tree)
        self.edges = {}

    def __repr__(self):
        if len(self.edges) > 0:
            return "({0!r})->{1!r}".format(self.data, self.edges)
        else:
            return "({0!r})".format(self.data)

    def predict(self, values):
        if len(self.edges) == 0:
            return self.data
        else:
            return self.edges[values[self.data]].predict(values)

    def maxDepth(self):
        if len(self.edges) == 0:
                return 0
        else:
            return 1 + max(e[1].maxDepth() for e in self.edges.items())

# hard coded for binary dataset
def entropy(s):
    if len(s) == 0:
        return 0

    pos = sum(1 for e in s if e.label == 1)
    neg = sum(1 for e in s if e.label == -1)
    pplus = pos / len(s)
    pminus = neg / len(s)

    safeLog = lambda a,b: 0 if a == 0 else math.log(a,b)

    return -pplus * safeLog(pplus,2) - pminus * safeLog(pminus,2)

def informationGain(s, a, impurityFunc):
    terms = []
    for v in [-1,1]:
        s_v = [e for e in s if e.attributes[a] == v]
        terms.append(len(s_v)/len(s) * impurityFunc(s_v))

    return impurityFunc(s) - sum(terms)

def id3(examples, attributes, k, remainingDepth):
    exampleLabels = {e.label for e in examples}
    if len(exampleLabels) == 1:
        return DecisionTree(next(iter(exampleLabels)))

    if remainingDepth == 0:
        # return a node with data set to the most common label
        return DecisionTree(sign(sum([e.label for e in examples])))

    bestAttribute = max(((a, informationGain(examples, a, entropy)) for a in numpy.random.choice(list(attributes), k, False)), key=lambda t: t[1])[0]
    root = DecisionTree(bestAttribute)
    for v in [0,1]:
        examples_v = [e for e in examples if e.attributes[bestAttribute] == v]
        if len(examples_v) == 0:
            # make node with data set to the most common label
            root.edges[v] = DecisionTree(sign(sum([e.label for e in examples])))
        else:
            root.edges[v] = id3(examples_v, attributes - {bestAttribute}, k, remainingDepth - 1)

    return root

def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    s_parser = subparsers.add_parser("test", help="Create an svm and test it.")
    s_parser.add_argument("-r", "--learningRate", help="Initial learning rate (gamma). default=0.01",
            type=float, default=0.01)
    s_parser.add_argument("-C", help="C hyperparameter. default=1",
            type=float, default=1)
    s_parser.add_argument("-e", "--epochs", help="Number of training epochs. default=1",
            type=int, default=1)
    s_parser.add_argument("trainingDataFile")
    s_parser.add_argument("trainingLabelFile")
    s_parser.add_argument("testDataFile")
    s_parser.add_argument("testLabelFile")
    s_parser.set_defaults(func=runTest)


    c_parser = subparsers.add_parser("cross", help="Run k-fold cross validation.")
    c_parser.add_argument("-k", "--kfolds", type=int, default=5, help="Number of folds. default=5")
    c_parser.add_argument("-r", "--learningRate", nargs="+", type=float, default=[0.01], help="Specify a list of learning rates to test. default=[0.01]")
    c_parser.add_argument("-C", help="C hyperparameter. default=1",
            type=float, default=1)
    c_parser.add_argument("-e", "--epochs", help="Number of training epochs. default=1",
            type=int, default=1)
    c_parser.add_argument("dataFile")
    c_parser.add_argument("labelFile")
    c_parser.set_defaults(func=runCross)

    f_parser = subparsers.add_parser("forest", help="Construct random forest and produce transformed featureset.")
    f_parser.add_argument("-N", type=int, default=5, help="Number of decision trees")
    f_parser.add_argument("-k", type=int, default=8, help="Number of random features to select for each tree node")
    f_parser.add_argument("dataFile")
    f_parser.add_argument("labelFile")
    f_parser.add_argument("transformFiles", nargs="+")
    f_parser.set_defaults(func=runForest)

    args = parser.parse_args()
    args.func(args)
    return 0

def svmUpdate(w, r, C, example):
    if example.label * w.dot(example.attributes) <= 1:
        w = (1-r)*w + r*C*example.label*example.attributes
    else:
        w = (1-r)*w

    return w

def svm(examples, r0, C, epochs):
    w = numpy.zeros(len(examples[0].attributes))
    r = r0
    t = 1

    for epoch in range(epochs):
        numpy.random.shuffle(examples)
        for example in examples:
            w = svmUpdate(w, r, C, example)
            r = r0/(1+r0*t/C)
            t += 1

    return w

def sign(x):
    if x >= 0:
        return 1
    else:
        return -1

def trainAndTest(trainingData, testData, r, C, epochs):
    svmVector  = svm(trainingData, r, C, epochs)

    truePositives = 0
    trueNegatives = 0
    falsePositives = 0
    falseNegatives = 0
    good = 0
    for d in testData:
        prediction = svmVector.dot(d.attributes)
        if prediction*d.label >= 0:
            good += 1
            if d.label >= 0:
                truePositives += 1
            else:
                trueNegatives += 1
        else:
            if d.label >= 0:
                falsePositives += 1
            else:
                falseNegatives += 1

    accuracy = (truePositives + trueNegatives)/len(testData)
    precision = 1
    if truePositives+trueNegatives > 0:
        precision = truePositives/(truePositives+trueNegatives)
    recall = 1
    if truePositives+falseNegatives > 0:
        recall = truePositives/(truePositives+falseNegatives)
    f1 = 2*precision*recall/(precision + recall)

    return (svmVector, accuracy, precision, recall, f1)

def runTest(args):
    print("Learning rate: {}, C: {}, epochs: {}\n".format(args.learningRate, args.C, args.epochs))
    print("Training on {}, {}".format(args.trainingDataFile, args.trainingLabelFile))
    print("Testing on {},{}".format(args.testDataFile, args.testLabelFile))

    trainingData = loadData(args.trainingDataFile, args.trainingLabelFile)
    testData = loadData(args.testDataFile, args.testLabelFile)

    result = trainAndTest(trainingData, testData, args.learningRate, args.C, args.epochs)
    # print("SVM Vector: {}".format(result[0]))
    print("accuracy: {}\nprecision: {}\nrecall: {}\nf1: {}".format(result[1], result[2], result[3], result[4]))

def runCross(args):
    data = loadData(args.dataFile, args.labelFile)
    print("C: {0}\n".format(args.C))

    rateResults = []
    for rate in args.learningRate:
        results = []
        # print("Testing learning rate {0}".format(rate))
        for i in range(args.kfolds):
            # print("    Testing on fold {0}".format(i))
            foldSize = int(len(data) / args.kfolds)
            foldIndex = foldSize*i
            trainingData = data[:foldIndex] + data[foldIndex+foldSize:]
            testData = data[foldIndex:foldIndex+foldSize]
            result = trainAndTest(trainingData, testData, rate, args.C, args.epochs)
            results.append(result[1])
            # print("    Updates: {0}".format(result[0][3]))
            # print("    Mistakes: {0}".format(result[0][2]))
            # print("    Accuracy: {0}/{1}={2}\n".format(result[1], result[2], result[3]))

        avg = statistics.mean(results)
        std = statistics.pstdev(results)
        # print("At rate {0}:\n    Mean: {1}\n    Standard deviation: {2}\n".format(rate, avg, std))
        rateResults.append((rate, avg, std))
    print("rate     | accuracy mean | accuracy std")
    for d in rateResults:
        print("{0:4f} | {1:13f} | {2:12f}".format(d[0], d[1], d[2]))

def runForest(args):
    data = loadData(args.dataFile, args.labelFile)
    print("Training on {}, {}".format(args.dataFile, args.labelFile))

    trees = trainTrees(data, args.N, args.k)


    for inFile in args.transformFiles:
        print("Transforming {}...".format(inFile))
        with open(inFile, "r") as dataF, open(inFile + "forest_" + str(args.N), "w") as outF:
            for d in dataF:
                e = Example(d.strip().split(" "), "0")
                # write a line for each set of tree predictions
                outF.write(" ".join([str(t.predict(e.attributes)) for t in trees]) + "\n")
    # correctPredictions  = sum(1 for d in testData if tree.predict(d.attributes) == d.label)
    # accuracy = correctPredictions/len(testData)
    # return (tree, correctPredictions, len(testData), accuracy)

    # print("Tree maximum depth: {0}".format(result[0].maxDepth()))
    # print("Accuracy: {0}/{1}={2}\n".format(result[1], result[2], result[3]))

def trainTrees(examples, N, k):
    trees = []
    for t in range(N):
        bag = numpy.random.choice(examples, len(examples))
        trees.append(id3(bag, set(range(len(examples[0].attributes))), k, math.inf))

    return trees


if __name__ == "__main__":
    main()

