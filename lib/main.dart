import 'package:flutter/material.dart';
import 'package:webview_flutter/webview_flutter.dart';
import 'package:url_launcher/url_launcher.dart';

void main() => runApp(MaterialApp(
  home: WebPage(),
  debugShowCheckedModeBanner: false,
));

class WebPage extends StatefulWidget {
  @override
  _WebPageState createState() => _WebPageState();
}

class _WebPageState extends State<WebPage> {
  late final WebViewController _controller;

  @override
  void initState() {
    super.initState();
    _controller = WebViewController()
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..loadRequest(Uri.parse("APP_URL_HERE"));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text("APP_NAME_HERE"),
        backgroundColor: Color(int.parse("APP_COLOR_HERE".replaceAll('#', '0xff'))),
        actions: [
          PopupMenuButton<int>(
            onSelected: (i) => launchUrl(Uri.parse("APP_DEV_HERE")),
            itemBuilder: (context) => [
              PopupMenuItem(value: 1, child: Text("Developer Channel")),
            ],
          ),
        ],
      ),
      body: WebViewWidget(controller: _controller),
    );
  }
}
