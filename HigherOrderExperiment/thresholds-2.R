c2 = read.csv("analyze/corr2.csv", header=F)

t2 = (1:60)*2
 

pdf("thresholdchart-2.pdf")
plot(t2 , c2$V1,xaxs="i", yaxs="i" , xlim=c(0,120), ylim=c(0.65,1),  col="black", pch=20, xlab="Threshold", ylab="R Squared")
grid(60,35,col="gray",lty=1)
abline(v=10,col="red")
abline(h=0.85,col="darkgreen")
points(t2 , c2$V1, col="black", pch=20)


dev.off()
