pths <- list.files('/home/tomnl/data/tomnl/WAX1/mzml', full.names = TRUE, pattern = ".*pos", recursive=T)
library(xcms)
library(camera)
library(msPurity)
pths <- pths[c(1,2, 6,7, 12,13)]
xset <- xcmsSet(pths, method='centWave', ppm=5)
xset <- group(xset, bw=1, mzwid=0.001, minfrac=0.5)
pa <- purityA(pths, cores = 3)
pa <- frag4feature(pa, xset, create_db=F)


xsa <- CAMERA::xsAnnotate(xset, nSlaves =3)
#Group after RT value of the xcms grouped peak
xsa <- CAMERA::groupFWHM(xsa)
xsa <- CAMERA::groupCorr(xsa)
xsa <- CAMERA::findIsotopes(xsa)
xsa <- CAMERA::findAdducts(xsa, polarity = 'positive')

db_pth <- create_database(pa, xset=NULL, xsa=xsa, out_dir='.')

db_pth2 <- spectral_matching(db_pth, cores=3)
purityX(xset, saveEIC = TRUE, sqlitePth = db_pth, xgroups = 1:500)
