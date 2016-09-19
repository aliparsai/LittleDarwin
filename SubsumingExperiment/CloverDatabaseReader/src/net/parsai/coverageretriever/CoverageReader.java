package net.parsai.coverageretriever;

import com.atlassian.clover.CloverDatabase;
import com.atlassian.clover.CoverageDataSpec;
import com.atlassian.clover.api.registry.FileInfo;
import com.atlassian.clover.api.registry.MethodInfo;
import com.atlassian.clover.api.registry.ProjectInfo;
import com.atlassian.clover.api.registry.StatementInfo;
import com.atlassian.clover.registry.entities.FullStatementInfo;
import com.atlassian.clover.registry.entities.TestCaseInfo;

import java.io.PrintStream;
import java.util.Set;


public class CoverageReader {

	public static void main(String[] args) throws Exception {
		if (args.length == 1 && args[0].equals("--server") ) {
			CoverageReaderPy4JServer server = new CoverageReaderPy4JServer();
			server.start();
		}
		else if (args.length == 3) {

			CloverDatabase db = CloverDatabase.loadWithCoverage(args[0], new CoverageDataSpec());
			String filename = args[1];
			int lineNumber = Integer.parseInt(args[2]);

			printCoveredTestsForStatement(db, filename, lineNumber, System.out);
		} else {
			System.err.println("Usage:");
			System.err.println("java " + CoverageReader.class.getName() + " database filename linenumber");
		}
	}

	private static void printCoveredTestsForStatement(CloverDatabase db, String filename, int lineNumber, PrintStream out)
	{
		ProjectInfo projectInfo = db.getRegistry().getProject();
		FileInfo fileInfo = projectInfo.findFile(filename);
		StatementInfo prevStmtInfo = null;
		Set<TestCaseInfo> testSet;
		for (MethodInfo methodInfo : fileInfo.getAllMethods())
			for (StatementInfo stmtInfo : methodInfo.getStatements()){
				if (stmtInfo.getStartLine() == lineNumber) {
					testSet = db.getTestHits((FullStatementInfo) stmtInfo);
					out.println(testSet.size());
					for (TestCaseInfo testCase : testSet) {
						out.println(testCase.getQualifiedName());
					}
				}

				if (prevStmtInfo != null && stmtInfo.getStartLine() >  lineNumber && prevStmtInfo.getStartLine() < lineNumber )
				{
					testSet = db.getTestHits((FullStatementInfo) prevStmtInfo);
					out.println(testSet.size());
					for (TestCaseInfo testCase : testSet) {
						out.println(testCase.getQualifiedName());
					}
				}

				prevStmtInfo = stmtInfo;
			}
	}
}
