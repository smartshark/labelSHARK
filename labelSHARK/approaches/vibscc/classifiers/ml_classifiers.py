from abc import ABCMeta, abstractmethod
from labelSHARK.approaches.vibscc.utils.pre_process_utils import stemmer_tokenizer,stemmer_tokenizer_message
from labelSHARK.approaches.vibscc.utils.mongo_pandas_utils import DataFrameColumnExtracter
from sklearn.feature_extraction.text import CountVectorizer
from nltk.corpus import stopwords
import string
# ml-classification-bug
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import LinearSVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline, make_pipeline, make_union, FeatureUnion
import numpy as np

class IMLClassifier(metaclass=ABCMeta):
    """Interface for classifiers which require training beforehand"""

    @abstractmethod
    def train_model(self, df, classType):
        pass

    @abstractmethod
    def classify_commit(self, df):
        pass


class NB_Classifier(IMLClassifier):

    def train_model(self, df, classType):

        message_pipeline = make_pipeline(
            DataFrameColumnExtracter('message'),
            CountVectorizer(tokenizer=stemmer_tokenizer_message(),
                            stop_words=stopwords.words('english') + list(string.punctuation))
        )

        files_pipeline = make_pipeline(
            DataFrameColumnExtracter('paths'),
            CountVectorizer(tokenizer=stemmer_tokenizer())
        )

        issue_type_pipeline = make_pipeline(
            DataFrameColumnExtracter('issue_type'),
            CountVectorizer(tokenizer=stemmer_tokenizer())
        )

        # weight components in FeatureUnion

        feature_union = FeatureUnion(
            transformer_list=[('message_pipe', message_pipeline), ('files_pipe', files_pipeline),
                              ('issue_pipe', issue_type_pipeline)],
            transformer_weights={
                'message_pipe': 1.0,
                'files_pipe': 1.0,
                'issue_pipe': 1.0
            }
        )

        self._feature_union = feature_union
        message_files_train_tdm = self._feature_union.fit_transform(df)
        class_train = df.iloc[:][classType].values

        self._nb = MultinomialNB()
        self._nb.fit(message_files_train_tdm, class_train)


    def classify_commit(self, df):

        message_files_test_tdm = self._feature_union.transform(df)
        class_predicted = self._nb.predict(message_files_test_tdm)
        return class_predicted


class MLP_Classifier(IMLClassifier):

    def train_model(self, df, classType):
        message_pipeline = make_pipeline(
            DataFrameColumnExtracter('message'),
            CountVectorizer(tokenizer=stemmer_tokenizer_message(),
                            stop_words=stopwords.words('english') + list(string.punctuation))
        )

        files_pipeline = make_pipeline(
            DataFrameColumnExtracter('paths'),
            CountVectorizer(tokenizer=stemmer_tokenizer())
        )

        issue_type_pipeline = make_pipeline(
            DataFrameColumnExtracter('issue_type'),
            CountVectorizer(tokenizer=stemmer_tokenizer())
        )

        # weight components in FeatureUnion

        feature_union = FeatureUnion(
            transformer_list=[('message_pipe', message_pipeline), ('files_pipe', files_pipeline),
                              ('issue_pipe', issue_type_pipeline)],
            transformer_weights={
                'message_pipe': 1.0,
                'files_pipe': 1.0,
                'issue_pipe': 1.0
            }
        )

        self._feature_union = feature_union
        message_files_train_tdm = self._feature_union.fit_transform(df)
        class_train = df.iloc[:][classType].values

        noNeurons = message_files_train_tdm.A.shape[1]
        self._mlp = MLPClassifier(hidden_layer_sizes=(noNeurons))
        self._mlp.fit(message_files_train_tdm, class_train)

    def classify_commit(self, df):

        message_files_test_tdm = self._feature_union.transform(df)
        class_predicted = self._mlp.predict(message_files_test_tdm)
        return class_predicted


class SVM_Classifier(IMLClassifier):
    def train_model(self, df, classType):
        message_pipeline = make_pipeline(
            DataFrameColumnExtracter('message'),
            CountVectorizer(tokenizer=stemmer_tokenizer_message(),
                            stop_words=stopwords.words('english') + list(string.punctuation))
        )

        files_pipeline = make_pipeline(
            DataFrameColumnExtracter('paths'),
            CountVectorizer(tokenizer=stemmer_tokenizer())
        )

        issue_type_pipeline = make_pipeline(
            DataFrameColumnExtracter('issue_type'),
            CountVectorizer(tokenizer=stemmer_tokenizer())
        )

        # weight components in FeatureUnion

        feature_union = FeatureUnion(
            transformer_list=[('message_pipe', message_pipeline), ('files_pipe', files_pipeline),
                              ('issue_pipe', issue_type_pipeline)],
            transformer_weights={
                'message_pipe': 1.0,
                'files_pipe': 1.0,
                'issue_pipe': 1.0
            }
        )

        self._feature_union = feature_union
        message_files_train_tdm = self._feature_union.fit_transform(df)
        class_train = df.iloc[:][classType].values

        self._svc = LinearSVC()
        self._svc.fit(message_files_train_tdm, class_train)

    def classify_commit(self, df):

        message_files_test_tdm = self._feature_union.transform(df)
        class_predicted = self._svc.predict(message_files_test_tdm)
        return class_predicted


class RF_Classifier(IMLClassifier):
    def train_model(self, df, classType):
        message_pipeline = make_pipeline(
            DataFrameColumnExtracter('message'),
            CountVectorizer(tokenizer=stemmer_tokenizer_message(),
                            stop_words=stopwords.words('english') + list(string.punctuation))
        )

        files_pipeline = make_pipeline(
            DataFrameColumnExtracter('paths'),
            CountVectorizer(tokenizer=stemmer_tokenizer())
        )

        issue_type_pipeline = make_pipeline(
            DataFrameColumnExtracter('issue_type'),
            CountVectorizer(tokenizer=stemmer_tokenizer())
        )

        # weight components in FeatureUnion

        feature_union = FeatureUnion(
            transformer_list=[('message_pipe', message_pipeline), ('files_pipe', files_pipeline),
                              ('issue_pipe', issue_type_pipeline)],
            transformer_weights={
                'message_pipe': 1.0,
                'files_pipe': 1.0,
                'issue_pipe': 1.0
            }
        )

        self._feature_union = feature_union
        message_files_train_tdm = self._feature_union.fit_transform(df)
        class_train = df.iloc[:][classType].values

        self._rf = RandomForestClassifier()
        self._rf.fit(message_files_train_tdm, class_train)

    def classify_commit(self, df):

        message_files_test_tdm = self._feature_union.transform(df)
        class_predicted = self._rf.predict(message_files_test_tdm)
        return class_predicted


class LR_Classifier(IMLClassifier):
    def train_model(self, df, classType):
        message_pipeline = make_pipeline(
            DataFrameColumnExtracter('message'),
            CountVectorizer(tokenizer=stemmer_tokenizer_message(),
                            stop_words=stopwords.words('english') + list(string.punctuation))
        )

        files_pipeline = make_pipeline(
            DataFrameColumnExtracter('paths'),
            CountVectorizer(tokenizer=stemmer_tokenizer())
        )

        issue_type_pipeline = make_pipeline(
            DataFrameColumnExtracter('issue_type'),
            CountVectorizer(tokenizer=stemmer_tokenizer())
        )

        # weight components in FeatureUnion

        feature_union = FeatureUnion(
            transformer_list=[('message_pipe', message_pipeline), ('files_pipe', files_pipeline),
                              ('issue_pipe', issue_type_pipeline)],
            transformer_weights={
                'message_pipe': 1.0,
                'files_pipe': 1.0,
                'issue_pipe': 1.0
            }
        )

        self._feature_union = feature_union
        message_files_train_tdm = self._feature_union.fit_transform(df)
        class_train = df.iloc[:][classType].values

        self._lr = LogisticRegression()
        self._lr.fit(message_files_train_tdm,class_train)

    def classify_commit(self, df):

        message_files_test_tdm = self._feature_union.transform(df)
        class_predicted = self._lr.predict(message_files_test_tdm)
        return class_predicted

class ML_Classifiers_Exec():
    """Class for training different machine-learning models and classifying commit"""
    def __init__(self, df):
        self._df = df.copy()
        self._class_list = ["BugFix", "Refactoring", "Test", "Feature", "Documentation", "Maintainance"]
        self._nb_class_list = ["Refactoring"]
        self._mlp_class_list = ["BugFix","Documentation", "Feature"]
        self._svm_class_list = ["BugFix", "Refactoring", "Test","Maintainance"]
        self._rf_class_list = ["Test","Maintainance"]
        self._lr_class_list = ["Documentation"]

        self._nb_classifiers = {}
        self._mlp_classifiers = {}
        self._svm_classifiers = {}
        self._rf_classifiers = {}
        self._lr_classifiers = {}

    def train_classifiers(self):
        """Sample training data and train classifiers"""
        for class_type in self._class_list:
            replace = False
            fn = lambda obj: obj.loc[np.random.choice(obj.index, size, replace), :]
            if (class_type == "BugFix"):
                size = 285  # sample size
                df_bugfix = self._df.groupby('BugFix', as_index=False).apply(fn)
                self._check_train_classifiers(class_type, df_bugfix)

            elif (class_type == "Refactoring"):
                size = 55
                df_refactoring = self._df.groupby('Refactoring', as_index=False).apply(fn)
                self._check_train_classifiers(class_type, df_refactoring)

            elif (class_type == "Test"):
                size = 258
                df_test = self._df.groupby('Test', as_index=False).apply(fn)
                self._check_train_classifiers(class_type, df_test)

            elif (class_type == "Feature"):
                size = 71
                df_feature = self._df.groupby('Feature', as_index=False).apply(fn)
                self._check_train_classifiers(class_type, df_feature)

            elif (class_type == "Documentation"):
                self._check_train_classifiers(class_type, self._df)

            elif (class_type == "Maintainance"):
                size = 251
                df_maintainance = self._df.groupby('Maintainance', as_index=False).apply(fn)
                self._check_train_classifiers(class_type, df_maintainance)

    def _check_train_classifiers(self, class_type, sample_df):
        """Train the model for specific label(class-type) if present"""
        if class_type in self._nb_class_list:
            nb_classifier = NB_Classifier()
            nb_classifier.train_model(sample_df, class_type)
            self._nb_classifiers[class_type] = nb_classifier

        if class_type in self._mlp_class_list:
            mlp_classifier = MLP_Classifier()
            mlp_classifier.train_model(sample_df, class_type)
            self._mlp_classifiers[class_type] = mlp_classifier

        if class_type in self._svm_class_list:
            svm_classifier = SVM_Classifier()
            svm_classifier.train_model(sample_df, class_type)
            self._svm_classifiers[class_type] = svm_classifier

        if class_type in self._rf_class_list:
            rf_classifier = RF_Classifier()
            rf_classifier.train_model(sample_df, class_type)
            self._rf_classifiers[class_type] = rf_classifier

        if class_type in self._lr_class_list:
            lr_classifier = LR_Classifier()
            lr_classifier.train_model(sample_df, class_type)
            self._lr_classifiers[class_type] = lr_classifier


    def get_all_labels(self, df):
        """Get all labels(class-type) from all classifiers"""
        labels = {}
        for class_type in self._class_list:

            if (class_type == "BugFix"):
                label = self._get_labels(class_type, df)
                labels[class_type] = label

            elif (class_type == "Refactoring"):
                label = self._get_labels(class_type, df)
                labels[class_type] = label

            elif (class_type == "Test"):
                label = self._get_labels(class_type, df)
                labels[class_type] = label

            elif (class_type == "Feature"):
                label = self._get_labels(class_type, df)
                labels[class_type] = label

            elif (class_type == "Documentation"):
                label = self._get_labels(class_type, df)
                labels[class_type] = label

            elif (class_type == "Maintainance"):
                label = self._get_labels(class_type, df)
                labels[class_type] = label

        return labels



    def _get_labels(self, class_type, df):
        """Get specific lable(class-type) from all classifiers"""
        labels = []
        if class_type in self._nb_class_list:
            label = self._nb_classifiers[class_type].classify_commit(df)
            labels.extend(label.tolist())

        if class_type in self._mlp_class_list:
            label = self._mlp_classifiers[class_type].classify_commit(df)
            labels.extend(label.tolist())

        if class_type in self._svm_class_list:
            label = self._svm_classifiers[class_type].classify_commit(df)
            labels.extend(label.tolist())

        if class_type in self._rf_class_list:
            label = self._rf_classifiers[class_type].classify_commit(df)
            labels.extend(label.tolist())

        if class_type in self._lr_class_list:
            label = self._lr_classifiers[class_type].classify_commit(df)
            labels.extend(label.tolist())

        return labels