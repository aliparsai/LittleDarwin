c2 = read.csv("analyze/corr2.csv", header=F)
c3 = read.csv("analyze/corr3.csv", header=F)
c4 = read.csv("analyze/corr4.csv", header=F)
c5 = read.csv("analyze/corr5.csv", header=F)
c6 = read.csv("analyze/corr6.csv", header=F)
c8 = read.csv("analyze/corr8.csv", header=F)

t2 = (1:60)*2
t3 = (1:40)*3
t4 = (1:30)*4
t5 = (1:24)*5
t6 = (1:20)*6
t8 = (1:15)*8
 

pdf("thresholdchart.pdf")
plot(t2 , c2$V1,xaxs="i", yaxs="i" , xlim=c(0,120), ylim=c(0,1),  col="black", pch=20, xlab="Threshold", ylab="R Squared")
grid(60,50,col="gray",lty=1)
points(t2 , c2$V1, col="black", pch=20)
points(t3 , c3$V1, col="blue", pch=20)
points(t4 , c4$V1, col="red", pch=20)
points(t5 , c5$V1, col="turquoise", pch=20)
points(t6 , c6$V1, col="purple", pch=20)
points(t8 , c8$V1, col="darkgreen", pch=20)


dev.off()
