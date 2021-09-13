import ezpubmed as ez
import utils_nlp

if __name__ == '__main__':
    p = ez.EzPubMed()
    p.update_db()

    # load zotero papers
    dfz = utils_nlp.initialize_zotero_library("Specific.json")
    dfv = utils_nlp.generate_zotero_embeddings(df)
    embedding = utils_nlp.calculate_embedding(dfv)