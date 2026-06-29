import 'package:flutter/material.dart';
import 'package:webview_flutter/webview_flutter.dart';

void main() => runApp(const MyApp());

class MyApp extends StatelessWidget {
  const MyApp({super.key});
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      home: Scaffold(
        appBar: AppBar(
          title: const Text('APP_NAME_PLACEHOLDER'), // এখানে অ্যাপের নাম বসবে
          backgroundColor: Colors.blue,
        ),
        body: WebViewWidget(
          controller: WebViewController()
            ..setJavaScriptMode(JavaScriptMode.unrestricted)
            ..loadRequest(Uri.parse('URL_PLACEHOLDER')), // এখানে ওয়েবসাইট লিঙ্ক বসবে
        ),
      ),
    );
  }
}
