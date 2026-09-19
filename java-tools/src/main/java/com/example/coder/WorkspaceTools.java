package com.example.coder;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import java.util.stream.Stream;
import org.springframework.ai.tool.annotation.Tool;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

@Service
public class WorkspaceTools {
 private final Path root;
 private final ApprovalService approvals;

 public WorkspaceTools(@Value("${workspace.root:/workspaces}") String root,ApprovalService approvals) throws IOException {
  this.root=Path.of(root).toAbsolutePath().normalize();this.approvals=approvals;
  Files.createDirectories(this.root);
 }

 private Path workspace(String taskId) throws IOException {
  if(!taskId.matches("[A-Za-z0-9_-]+")) throw new IllegalArgumentException("invalid task id");
  Path w=root.resolve(taskId).normalize();
  if(!w.startsWith(root)) throw new SecurityException("workspace escape");
  if(!Files.exists(w)) seed(w);
  return w;
 }

 private Path safe(Path w,String relative) {
  if(relative==null||relative.isBlank()) throw new IllegalArgumentException("empty path");
  Path p=w.resolve(relative).normalize();
  if(!p.startsWith(w)) throw new SecurityException("path traversal denied");
  String s=p.toString();
  if(s.contains(File.separator+".git"+File.separator)||p.getFileName().toString().equals(".git"))
   throw new SecurityException(".git access denied");
  return p;
 }

 private void seed(Path w) throws IOException {
  Files.createDirectories(w.resolve("src/main/java/demo"));
  Files.createDirectories(w.resolve("src/test/java/demo"));
  Files.writeString(w.resolve("pom.xml"),"""
<project xmlns="http://maven.apache.org/POM/4.0.0">
 <modelVersion>4.0.0</modelVersion><groupId>demo</groupId><artifactId>refund-demo</artifactId><version>1.0</version>
 <properties><maven.compiler.source>21</maven.compiler.source><maven.compiler.target>21</maven.compiler.target><project.build.sourceEncoding>UTF-8</project.build.sourceEncoding><junit.version>5.11.4</junit.version></properties>
 <dependencies><dependency><groupId>org.junit.jupiter</groupId><artifactId>junit-jupiter</artifactId><version>${junit.version}</version><scope>test</scope></dependency></dependencies>
 <build><plugins><plugin><groupId>org.apache.maven.plugins</groupId><artifactId>maven-surefire-plugin</artifactId><version>3.5.2</version></plugin></plugins></build>
</project>
""");
  Files.writeString(w.resolve("src/main/java/demo/RefundService.java"),"""
package demo;
public class RefundService {
 public long refund(long amountCents) {
  return amountCents;
 }
}
""");
  Files.writeString(w.resolve("src/test/java/demo/RefundServiceTest.java"),"""
package demo;
import static org.junit.jupiter.api.Assertions.*;
import org.junit.jupiter.api.Test;
class RefundServiceTest {
 @Test void positiveRefund(){assertEquals(100,new RefundService().refund(100));}
}
""");
  run(List.of("git","init"),w,20);
  run(List.of("git","config","user.email","agent@example.local"),w,10);
  run(List.of("git","config","user.name","Coding Agent Demo"),w,10);
  run(List.of("git","add","."),w,10);
  run(List.of("git","commit","-m","baseline"),w,20);
 }

 @Tool(description="List repository files. Read-only.")
 public List<String> repo_tree(String task_id) throws IOException {
  Path w=workspace(task_id);
  try(Stream<Path> s=Files.walk(w,8)){
   return s.filter(Files::isRegularFile).filter(p->!p.toString().contains(File.separator+".git"+File.separator))
    .map(w::relativize).map(Path::toString).sorted().limit(500).toList();
  }
 }

 @Tool(description="Search source text for a literal query. Read-only.")
 public List<String> search_code(String task_id,String query) throws IOException {
  if(query==null||query.length()>200) throw new IllegalArgumentException("invalid query");
  Path w=workspace(task_id);List<String> out=new ArrayList<>();
  for(String rel:repo_tree(task_id)){
   Path p=safe(w,rel);
   if(Files.size(p)>1_000_000) continue;
   String text=Files.readString(p);
   String[] lines=text.split("\\R");
   for(int i=0;i<lines.length;i++) if(lines[i].contains(query)){
    out.add(rel+":"+(i+1)+": "+lines[i].trim()); if(out.size()>=100)return out;
   }
  }
  return out;
 }

 @Tool(description="Read a UTF-8 repository file. Read-only.")
 public String read_file(String task_id,String path) throws IOException {
  Path p=safe(workspace(task_id),path);
  if(!Files.exists(p)||!Files.isRegularFile(p)) return "NOT_FOUND";
  if(Files.size(p)>500_000) return "DENIED: file too large";
  return Files.readString(p);
 }

 @Tool(description="Write a UTF-8 repository file. Requires task-scoped human approval token.")
 public String write_file(String task_id,String path,String content,String approval_token) throws IOException {
  if(!approvals.valid(approval_token,task_id)) return "DENIED: valid task approval required";
  Path p=safe(workspace(task_id),path);
  if(path.endsWith(".env")||path.toLowerCase().contains("secret")) return "DENIED: sensitive path";
  if(content.length()>500_000) return "DENIED: content too large";
  Files.createDirectories(p.getParent());Files.writeString(p,content,StandardCharsets.UTF_8);
  return "WROTE "+path+" bytes="+content.getBytes(StandardCharsets.UTF_8).length;
 }

 @Tool(description="Run the repository's allowlisted build and tests. No arbitrary command input.")
 public String run_build(String task_id) throws IOException,InterruptedException {
  Path w=workspace(task_id);
  if(Files.exists(w.resolve("pom.xml"))) return run(List.of("mvn","-q","test"),w,120);
  return "NO_SUPPORTED_BUILD_FILE";
 }

 @Tool(description="Return current git diff. Read-only.")
 public String git_diff(String task_id) throws IOException,InterruptedException {
  return run(List.of("git","diff","--no-ext-diff"),workspace(task_id),20);
 }

 private String run(List<String> command,Path cwd,int seconds) throws IOException {
  try{
   Process p=new ProcessBuilder(command).directory(cwd.toFile()).redirectErrorStream(true).start();
   boolean done=p.waitFor(seconds,java.util.concurrent.TimeUnit.SECONDS);
   if(!done){p.destroyForcibly();return "TIMEOUT";}
   String output=new String(p.getInputStream().readAllBytes(),StandardCharsets.UTF_8);
   return "EXIT="+p.exitValue()+"\n"+output.substring(0,Math.min(output.length(),20000));
  }catch(InterruptedException e){Thread.currentThread().interrupt();return "INTERRUPTED";}
 }
}