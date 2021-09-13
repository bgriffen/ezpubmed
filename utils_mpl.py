from matplotlib.widgets import RectangleSelector
from matplotlib.widgets import LassoSelector
import matplotlib.colors as clr
from matplotlib.path import Path
from matplotlib.patches import Rectangle, Ellipse,Polygon
import numpy as np
from matplotlib.ticker import MaxNLocator

class Highlighter(object):

    def __init__(self, ax_umap, ax_year, ax_mesh, dfpapers, colors='c', method='lasso', add_text=False,index_list=None,include_nlp=False):
        self.ax_umap = ax_umap
        self.ax_year = ax_year
        self.ax_mesh = ax_mesh
        self.canvas_umap = ax_umap.figure.canvas
        self.canvas_year = ax_year.figure.canvas
        self.canvas_mesh = ax_mesh.figure.canvas
        self.x, self.y = dfpapers['umap-x'], dfpapers['umap-y']
        self.add_text = add_text
        self.df_papers = dfpapers
        self.df_selected = None
        #self.selected_text = None
        self.full_index = dfpapers.index.values
        highlight_color = colors
        highlight_size = 20
        self.object_index = None
        self.mask = np.zeros(self.x.shape[0], dtype=bool)
        self.scaled_rgb = (65 / 256., 91 / 256., 169 / 256.)
        self.selection_method = method
        self.x0 = None
        self.y0 = None
        self.x1 = None
        self.y1 = None
        self.entities_dict = {}
        self._highlight = ax_umap.scatter(
           [],[], marker="o", lw=0, s=highlight_size, c=highlight_color
        )
        self.include_nlp = include_nlp
        if include_nlp:
            self.nlp = spacy.load('en_ner_bionlp13cg_md')
            self.nlp.add_pipe(self.nlp.create_pipe('sentencizer'))
        #if self.selected_text != None:
        #    self.selected_text.remove()

        if self.add_text:
            self.selected_text = self.ax_umap.text(
                0.03,
                0.97,
                "%3.2f (%i events)" % (0, 0),
                ha="left",
                va="top",
                transform=self.ax_umap.transAxes,
                color="k",
                fontname="Helvetica",
            )

        self.name_to_selector = {"lasso": LassoSelector}
        selector = self.name_to_selector[method.lower()]

        onselect_dict = {
            LassoSelector: self._onselect_lasso,
        }

        self.lasso = selector(self.ax_umap, onselect_dict[selector])

    # def remove_text(self):

    def disconnect(self):
        self.canvas_umap.mpl_disconnect(self.lasso)

    def _draw_points(self):
        self.object_index = self.full_index[self.mask]
        self.nevents = len(self.mask)
        self.nselected = np.sum(self.mask)
        if self.add_text:
            self.selected_text.remove()
            
        if self.add_text:
            self.selected_text = self.ax_umap.text(
                0.03,
                0.97,
                "%3.2f (%i events)"
                % (self.nselected * 100. / self.nevents, self.nselected),
                ha="left",
                va="top",
                transform=self.ax_umap.transAxes,
                color="k",
                fontname="Helvetica",
            )
        xy = np.column_stack([self.x[self.mask], self.y[self.mask]])
        self._highlight.set_offsets(xy)
        self.canvas_umap.draw()


    def _onselect_lasso(self, verts):
        self.verts = np.array(verts)
        p = Path(self.verts)
        pix = np.array([self.x, self.y]).T
        self.mask = p.contains_points(pix, radius=0)
        self._draw_points()
        self.df_selected = self.df_papers[self.mask]
        print("%s selected" % self.df_selected.shape[0])
        if self.df_selected.shape[0] == 0:
            self.entities_dict = {}

        
        self.ax_mesh.clear()
        self.ax_year.clear()

        mterms = []
        for idx in self.df_selected.index:
            yp = self.df_selected.loc[idx]['pubdate']
            mt = self.df_selected.loc[idx]['mesh_terms']
            t = self.df_selected.loc[idx]['title']
            #sdoc = self.nlp(self.df_selected.loc[idx]['abstract'])
            #sen = list(sdoc.sents)
            mterms.extend(sorted([mti.split(":")[-1] for mti in mt.split(";")]))
            print("(%s) %s" % (yp,t))
            doci = self.df_selected.loc[idx]['title'] + self.df_selected.loc[idx]['abstract']
            if self.include_nlp:
                sdoc = nlp(doci)
                #for si in sdoc.ents:
                self.entities_dict[idx] = sdoc.ents
            #print(" Mesh:",", ".join(mterms))
#            print(" ".join(item.split()[:100]))
        self.df_selected.to_csv("tmp_selected.csv")
        
        self.mesh_counts = Counter(mterms)
        self.mesh_counts_top = self.mesh_counts.most_common(50)
        dfcounts = pd.DataFrame.from_dict(dict(self.mesh_counts_top), orient='index')
        dfcounts.sort_values(0,inplace=True)
        if dfcounts.shape[0]!=0:
            dfcounts.plot(kind='barh',ax=self.ax_mesh,fontsize=6,legend=False)

        xmin = np.min(self.df_selected['pubdate'])
        xmax = np.max(self.df_selected['pubdate'])
        self.ax_year.hist(self.df_selected['pubdate'],bins=np.arange(xmin,xmax+1)-0.5)
        self.ax_year.set_xlim([xmin,xmax])
        self.ax_year.xaxis.set_major_locator(MaxNLocator(integer=True))
        for label in self.ax_year.get_xticklabels():
            label.set_rotation(45)
            label.set_fontsize(6)
            label.set_ha('right')

        self.canvas_year.draw()
        self.canvas_mesh.draw()
