fo = read.csv("analyze/fo-14.csv", header=F)
fop=fo$V3/fo$V4
so = read.csv("analyze/so-7.csv", header=F)
sop=so$V3/so$V4
pdf("chart.pdf")
curve(1-(1-x)^2,0,1,col="red", xlab="First-Order Mutation Coverage", ylab="Second-Order Mutation Coverage")
points(fop,sop,pch=20,col="blue")
dev.off()
