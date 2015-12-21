fo = read.csv("firstorder.csv", header=F)
fop=fo$V3/fo$V4
so = read.csv("secondorder.csv", header=F)
sop=so$V3/so$V4
pdf("chart.pdf")
curve(1-(1-x)^2,0,1,col="red")
points(fop,sop,pch=20,col="blue")
dev.off()
