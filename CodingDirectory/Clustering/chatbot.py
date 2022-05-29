#self.get_df_from_query(query, max_elems=query_max_elems)
#self.process_df_col(,

import pandas as pd

import solrhandler
import clusterer as cls
import topicdeterminator

class Chatbot:

    def __init__(self, solrhandler, clusterer, topicdeterminator):

        # Komponenten
        self.solrhandler = solrhandler
        self.clusterer = clusterer
        self.topicdeterminator = topicdeterminator

        self.query = None
        self.df: pd.DataFrame

        self.topicBlacklist = []

        self.nrow = None


    def initialQuery(self,query):
        self.query = query
        self.df = self.solrhandler.get_df_from_query(query)
        self.df = self.clusterer.run(self.df)
        self.df = self.topicdeterminator.run(self.df)


    def findCorrectAnswer(self,targetService):
        """
        :return: True: targetService is in Cluster which is to be asked about False: else
        """

        # Find Target Cluster
        temp = self.topicdeterminator.df
        clusteredColumn = self.clusterer.getClusteredColumn()
        service = temp.loc[temp["id"]==str(targetService)]
        targetCluster = service[clusteredColumn][0]

        #print("targetCluster "+ str(targetCluster) + "\nselectedCluster " + str(self.getSelectedClusterForQuestion()))
        if targetCluster == self.getSelectedClusterForQuestion():
            return True
        else:
            return False

    def refineResultset(self, answer):
        """
        :param clusterId:
        :param answer: True = yes, False = no
        :return:
        """

        #self.topicBlacklist = self.topicBlacklist + [self.getSelectedTopicForQuestion()] # Append topic to blacklist

        n_row_bef = len(self.df.index)
        # go into cluster if topic fits intent or discard cluster, if not
        if answer:
            self.df = self.df.loc[self.df[self.clusterer.getClusteredColumn()] == self.getSelectedClusterForQuestion()]#.reset_index()
        else:
            self.df = self.df.loc[self.df[self.clusterer.getClusteredColumn()] != self.getSelectedClusterForQuestion()]#.reset_index()
        n_row_aft = len(self.df.index)

        # check if finished
        self.is_finished = n_row_aft == n_row_bef or n_row_aft == 1 or n_row_aft == 0

        # Refine Cluster + Topics
        self.df = self.clusterer.run(self.df, firstCall = False)
        self.df = self.topicdeterminator.run(self.df) # TODO FEHLER wenn 2 mal aufgerufen

        if self.is_finished:
            return True
        else:
            return False

    def getSelectedClusterForQuestion(self):
        """

        :return: Cluster with most services
        """
        df_row = self.topicdeterminator.df_clus.sort_values(by = "count", ascending=False).head(1)
        #print(df_row[self.clusterer.getClusteredColumn()])
        return df_row[self.clusterer.getClusteredColumn()][1]

    def getSelectedTopicForQuestion(self):
        """

        :return:
        """
        df_row = self.topicdeterminator.df_clus.sort_values(by="count", ascending=False).head(1)

        return df_row["Topics"][1]

    def generateQuestion(self):
        """

        :return:
        """
        return "Geht es bei ihrem Anliegen um " + str(self.getSelectedTopicForQuestion())+ "?"