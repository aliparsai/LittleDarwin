grammar ConfigFile;
options {
    language=Python2;
}


start                       : statement* EOF ;
statement                   : boolStatement | intStatement | strStatement;

strStatement                : strOption EqualSign string EndLine ;
intStatement                : intOption EqualSign integer EndLine ;
boolStatement               : boolOption EqualSign boolean EndLine ;

strOption                   : StrOptionLiteral ;
intOption                   : IntOptionLiteral ;
boolOption                  : BoolOptionLiteral ;

StrOptionLiteral            : 'sourcepath' | 'buildpath' | 'buildcommand' | 'testpath' | 'testcommand'
                            | 'initialbuildcommand' | 'alternativedatabase' | 'cleanup' ;
IntOptionLiteral            : 'timeout' | 'higherorder' ;
BoolOptionLiteral           : 'mutate' | 'build' | 'verbose' ;


EqualSign          : '=' | ':' | '->' ;
EndLine            : ';' ;

integer                     :   IntegerLiteral ;
IntegerLiteral              :   [0-9]+ ;
boolean                     :   true | false ;
true                        :   TrueLiteral ;
false                       :   FalseLiteral ;
TrueLiteral                 :   'true' | 'True' | 'T' | 'Yes' | 'Y' | 'yes' | 'Active' | 'active' | 'Enable' | 'enable' ;
FalseLiteral                :   'false' | 'False' | 'F' | 'No' | 'N' | 'no' | 'Inactive' | 'inactive' | 'Disable' | 'disable' ;
string                      :   StringLiteral ;
StringLiteral               :   '"' StringCharacters? '"';
fragment StringCharacters   :   StringCharacter+ ;
fragment StringCharacter    :   ~["\\] | EscapeSequence ;
fragment EscapeSequence     :   '\\' [btnfr"'\\] | OctalEscape | UnicodeEscape ;

fragment OctalEscape        :   '\\' OctalDigit  | '\\' OctalDigit OctalDigit  |   '\\' ZeroToThree OctalDigit OctalDigit ;
fragment UnicodeEscape      :   '\\' 'u' HexDigit HexDigit HexDigit HexDigit ;
fragment ZeroToThree        :   [0-3] ;
fragment HexDigit           :   [0-9a-fA-F] ;
fragment OctalDigit         :   [0-8] ;


WS              :  [ \t\r\n\u000C]+ -> skip ;
COMMENT         :   '/*' .*? '*/' -> skip ;
LINE_COMMENT    :   '//' ~[\r\n]* -> skip ;

/*

optionParser.add_option("-m", "--mutate", action="store_true", dest="isMutationActive", default=False,
                            help="Activate the mutation phase.")
    optionParser.add_option("-b", "--build", action="store_true", dest="isBuildActive", default=False,
                            help="Activate the build phase.")
    optionParser.add_option("-v", "--verbose", action="store_true", dest="isVerboseActive", default=False,
                            help="Verbose output.")
    optionParser.add_option("-p", "--path", action="store", dest="sourcePath",
                            default=os.path.dirname(os.path.realpath(__file__)), help="Path to source files.")
    optionParser.add_option("-t", "--build-path", action="store", dest="buildPath",
                            default=os.path.dirname(os.path.realpath(__file__)), help="Path to build system working directory.")
    optionParser.add_option("-c", "--build-command", action="store", dest="buildCommand", default="mvn,test",
                            help="Command to run the build system. If it includes more than a single argument, they should be seperated by comma. For example: mvn,install")
    optionParser.add_option("--test-path", action="store", dest="testPath",
                            default="***dummy***", help="path to test project build system working directory")
    optionParser.add_option("--test-command", action="store", dest="testCommand", default="***dummy***",
                            help="Command to run the test-suite. If it includes more than a single argument, they should be seperated by comma. For example: mvn,test")
    optionParser.add_option("--initial-build-command", action="store", dest="initialBuildCommand",
                            default="***dummy***", help="Command to run the initial build.")
    optionParser.add_option("--timeout", type="int", action="store", dest="timeout", default=60,
                            help="Timeout value for the build process.")
    optionParser.add_option("--cleanup", action="store", dest="cleanUp", default="***dummy***",
                            help="Commands to run after each build.")
    optionParser.add_option("--use-alternate-database", action="store", dest="alternateDb", default="***dummy***",
                            help="Path to alternative database.")
    optionParser.add_option("--license", action="store_true", dest="isLicenseActive", default=False,
                            help="Output the license and exit.")
    optionParser.add_option("--higher-order", type="int", action="store", dest="higherOrder", default=1,
                            help="Define order of mutation. Use -1 to dynamically adjust per class.")


*/
