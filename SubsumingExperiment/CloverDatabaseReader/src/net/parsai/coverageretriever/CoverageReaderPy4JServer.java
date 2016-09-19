package net.parsai.coverageretriever;

import py4j.GatewayServer;

import com.atlassian.clover.CloverDatabase;
import com.atlassian.clover.CoverageDataSpec;
import com.atlassian.clover.api.CloverException;
import com.atlassian.clover.api.registry.FileInfo;
import com.atlassian.clover.api.registry.MethodInfo;
import com.atlassian.clover.api.registry.ProjectInfo;
import com.atlassian.clover.api.registry.StatementInfo;
import com.atlassian.clover.registry.entities.FullStatementInfo;
import com.atlassian.clover.registry.entities.TestCaseInfo;

import java.util.ArrayList;
import java.util.List;
import java.util.Set;

public class CoverageReaderPy4JServer {

	public CloverDatabase cloverDatabase;
	
	

	public CoverageReaderPy4JServer() {
		super();
		this.cloverDatabase = null;
	}

	public void openDB(String dbPath) throws CloverException {
		this.cloverDatabase = CloverDatabase.loadWithCoverage(dbPath, new CoverageDataSpec());
	}
	
	public void start() {
		GatewayServer gatewayServer = new GatewayServer(this);
		gatewayServer.start();
		System.out.println("Server Started");

	}

	public CoverageReaderPy4JServer getInstance() {
		return this;
	}

	public List<String> retrieveResults(String filename, int lineNumber) {
		ProjectInfo projectInfo = this.cloverDatabase.getRegistry().getProject();
		FileInfo fileInfo = projectInfo.findFile(filename);
		StatementInfo prevStmtInfo = null;
		Set<TestCaseInfo> testSet;
		ArrayList<String> statementList = new ArrayList<String>();

		for (MethodInfo methodInfo : fileInfo.getAllMethods())
			for (StatementInfo stmtInfo : methodInfo.getStatements()) {
				if (stmtInfo.getStartLine() == lineNumber) {
					testSet = this.cloverDatabase.getTestHits((FullStatementInfo) stmtInfo);
					statementList.add(Integer.toString(testSet.size()));
					for (TestCaseInfo testCase : testSet) {
						statementList.add(testCase.getQualifiedName());
					}
				}

				if (prevStmtInfo != null && stmtInfo.getStartLine() > lineNumber
						&& prevStmtInfo.getStartLine() < lineNumber) {
					testSet = this.cloverDatabase.getTestHits((FullStatementInfo) prevStmtInfo);
					statementList.add(Integer.toString(testSet.size()));
					for (TestCaseInfo testCase : testSet) {
						statementList.add(testCase.getQualifiedName());
					}
				}

				prevStmtInfo = stmtInfo;
			}

		return statementList;

	}

}
