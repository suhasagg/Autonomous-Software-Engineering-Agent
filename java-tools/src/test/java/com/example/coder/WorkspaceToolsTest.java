package com.example.coder;
import static org.junit.jupiter.api.Assertions.*;
import java.nio.file.Files;
import org.junit.jupiter.api.Test;
class WorkspaceToolsTest {
 @Test void traversalDenied() throws Exception {
  var dir=Files.createTempDirectory("coder-test");
  var a=new ApprovalService();var tools=new WorkspaceTools(dir.toString(),a);
  assertThrows(SecurityException.class,()->tools.read_file("TASK-1","../../etc/passwd"));
 }
 @Test void writeNeedsApproval() throws Exception {
  var dir=Files.createTempDirectory("coder-test");
  var a=new ApprovalService();var tools=new WorkspaceTools(dir.toString(),a);
  assertTrue(tools.write_file("TASK-1","x.txt","hello","bad").startsWith("DENIED"));
 }
}