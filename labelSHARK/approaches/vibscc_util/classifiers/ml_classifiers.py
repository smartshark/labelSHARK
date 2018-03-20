from abc import ABCMeta, abstractmethod
from ..utils.pre_process_utils import stemmer_tokenizer,stemmer_tokenizer_message
from ..utils.mongo_pandas_utils import DataFrameColumnExtracter
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
    def train_model(self, tdm, class_train):
        pass

    @abstractmethod
    def classify_commit(self, tdm):
        pass


class NB_Classifier(IMLClassifier):
    def train_model(self, tdm, class_train):
        self._nb = MultinomialNB()
        self._nb.fit(tdm, class_train)

    def classify_commit(self, tdm):
        class_predicted = self._nb.predict(tdm)
        return class_predicted


class MLP_Classifier(IMLClassifier):
    def train_model(self, tdm, class_train):
        no_neurons = tdm.A.shape[1]
        print("number of neurons", no_neurons)
        self._mlp = MLPClassifier(hidden_layer_sizes=(no_neurons))
        self._mlp.fit(tdm, class_train)

    def classify_commit(self, tdm):
        class_predicted = self._mlp.predict(tdm)
        return class_predicted


class SVM_Classifier(IMLClassifier):
    def train_model(self, tdm, class_train):
        self._svc = LinearSVC()
        self._svc.fit(tdm, class_train)

    def classify_commit(self, tdm):
        class_predicted = self._svc.predict(tdm)
        return class_predicted


class RF_Classifier(IMLClassifier):
    def train_model(self, tdm, class_train):
        self._rf = RandomForestClassifier()
        self._rf.fit(tdm, class_train)

    def classify_commit(self, tdm):
        class_predicted = self._rf.predict(tdm)
        return class_predicted


class LR_Classifier(IMLClassifier):
    def train_model(self, tdm, class_train):
        self._lr = LogisticRegression()
        self._lr.fit(tdm,class_train)

    def classify_commit(self, tdm):
        class_predicted = self._lr.predict(tdm)
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
                class_train, tdm =  self._get_features_class(class_type, df_bugfix)
                self._check_train_classifiers(class_type, tdm, class_train)

            elif (class_type == "Refactoring"):
                size = 55
                df_refactoring = self._df.groupby('Refactoring', as_index=False).apply(fn)
                class_train, tdm = self._get_features_class(class_type, df_refactoring)
                self._check_train_classifiers(class_type, tdm, class_train)

            elif (class_type == "Test"):
                size = 258
                df_test = self._df.groupby('Test', as_index=False).apply(fn)
                class_train, tdm = self._get_features_class(class_type, df_test)
                self._check_train_classifiers(class_type, tdm, class_train)

            elif (class_type == "Feature"):
                size = 71
                df_feature = self._df.groupby('Feature', as_index=False).apply(fn)
                class_train, tdm = self._get_features_class(class_type, df_feature)
                self._check_train_classifiers(class_type, tdm, class_train)

            elif (class_type == "Documentation"):
                class_train, tdm = self._get_features_class(class_type, self._df)
                self._check_train_classifiers(class_type, tdm, class_train)

            elif (class_type == "Maintainance"):
                size = 251
                df_maintainance = self._df.groupby('Maintainance', as_index=False).apply(fn)
                class_train, tdm = self._get_features_class(class_type, df_maintainance)
                self._check_train_classifiers(class_type, tdm, class_train)

    def _check_train_classifiers(self, class_type, sample_df, class_train):
        """Train the model for specific label(class-type) if present"""
        if class_type in self._nb_class_list:
            nb_classifier = NB_Classifier()
            nb_classifier.train_model(sample_df, class_train)
            self._nb_classifiers[class_type] = nb_classifier

        if class_type in self._mlp_class_list:
            mlp_classifier = MLP_Classifier()
            mlp_classifier.train_model(sample_df, class_train)
            self._mlp_classifiers[class_type] = mlp_classifier

        if class_type in self._svm_class_list:
            svm_classifier = SVM_Classifier()
            svm_classifier.train_model(sample_df, class_train)
            self._svm_classifiers[class_type] = svm_classifier

        if class_type in self._rf_class_list:
            rf_classifier = RF_Classifier()
            rf_classifier.train_model(sample_df, class_train)
            self._rf_classifiers[class_type] = rf_classifier

        if class_type in self._lr_class_list:
            lr_classifier = LR_Classifier()
            lr_classifier.train_model(sample_df, class_train)
            self._lr_classifiers[class_type] = lr_classifier


    def get_all_labels(self, df):
        """Get all labels(class-type) from all classifiers"""
        labels = {}
        for class_type in self._class_list:

            if (class_type == "BugFix"):
                tdm = self._get_features(df, class_type)
                label = self._get_labels(class_type, tdm)
                labels[class_type] = label

            elif (class_type == "Refactoring"):
                tdm = self._get_features(df, class_type)
                label = self._get_labels(class_type, tdm)
                labels[class_type] = label

            elif (class_type == "Test"):
                tdm = self._get_features(df, class_type)
                label = self._get_labels(class_type, tdm)
                labels[class_type] = label

            elif (class_type == "Feature"):
                tdm = self._get_features(df, class_type)
                label = self._get_labels(class_type, tdm)
                labels[class_type] = label

            elif (class_type == "Documentation"):
                tdm = self._get_features(df, class_type)
                label = self._get_labels(class_type, tdm)
                labels[class_type] = label

            elif (class_type == "Maintainance"):
                tdm = self._get_features(df, class_type)
                label = self._get_labels(class_type, tdm)
                labels[class_type] = label

        return labels



    def _get_labels(self, class_type, tdm):
        """Get specific lable(class-type) from all classifiers"""
        labels = []
        if class_type in self._nb_class_list:
            label = self._nb_classifiers[class_type].classify_commit(tdm)
            labels.extend(label.tolist())

        if class_type in self._mlp_class_list:
            label = self._mlp_classifiers[class_type].classify_commit(tdm)
            labels.extend(label.tolist())

        if class_type in self._svm_class_list:
            label = self._svm_classifiers[class_type].classify_commit(tdm)
            labels.extend(label.tolist())

        if class_type in self._rf_class_list:
            label = self._rf_classifiers[class_type].classify_commit(tdm)
            labels.extend(label.tolist())

        if class_type in self._lr_class_list:
            label = self._lr_classifiers[class_type].classify_commit(tdm)
            labels.extend(label.tolist())

        return labels


    def _get_features_class(self, class_type, df):
        "Extract features and class for training"
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

        class_train = df.iloc[:][class_type].values
        if (class_type == "BugFix"):
            self._bugfix_feature_union = feature_union
            message_files_train_tdm = self._bugfix_feature_union.fit_transform(df)
        elif (class_type == "Refactoring"):
            self._refactoring_feature_union = feature_union
            message_files_train_tdm = self._refactoring_feature_union.fit_transform(df)
        elif (class_type == "Test"):
            self._test_feature_union = feature_union
            message_files_train_tdm = self._test_feature_union.fit_transform(df)
        elif (class_type == "Feature"):
            self._feature_feature_union = feature_union
            message_files_train_tdm = self._feature_feature_union.fit_transform(df)
        elif (class_type == "Documentation"):
            self._documentation_feature_union = feature_union
            message_files_train_tdm = self._documentation_feature_union.fit_transform(df)
        elif (class_type == "Maintainance"):
            self._maintainence_feature_union = feature_union
            message_files_train_tdm = self._maintainence_feature_union.fit_transform(df)

        return class_train, message_files_train_tdm


    def _get_features(self, df, class_type):
        "Extract features for classification"
        if (class_type == "BugFix"):
            message_files_predict_tdm = self._bugfix_feature_union.transform(df)
        elif (class_type == "Refactoring"):
            message_files_predict_tdm = self._refactoring_feature_union.transform(df)
        elif (class_type == "Test"):
            message_files_predict_tdm = self._test_feature_union.transform(df)
        elif (class_type == "Feature"):
            message_files_predict_tdm = self._feature_feature_union.transform(df)
        elif (class_type == "Documentation"):
            message_files_predict_tdm = self._documentation_feature_union.transform(df)
        elif (class_type == "Maintainance"):
            message_files_predict_tdm = self._maintainence_feature_union.transform(df)

        return message_files_predict_tdm