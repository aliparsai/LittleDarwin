fo = read.csv("analyze/fo-60.csv", header=F)
fop=fo$V3/fo$V4
to = read.csv("analyze/to-20.csv", header=F)
top=to$V3/to$V4
pdf("chart2.pdf")
curve(1-(1-x)^3,0,1,col="red", xlab="First-Order Mutation Coverage", ylab="Third-Order Mutation Coverage")
points(fop,top,pch=20,col="blue")
dev.off()
