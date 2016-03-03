django-elasticindex
~~~~~~~~~~~~~~~~~~~

Django用 Elasticsearch の薄いラッパー


できること
=====

・Django モデルと対応させ、Elasticsearch にデータを流し込むことができます。

(モデルとの対応は必須ではありません)

・Djangoクエリセットに少し近い形式で、クエリを発行することができます。

クエリには Elasticsearch のクエリに用いるための辞書をそのまま用いる、
あまり分厚くない(お節介の少ない)インターフェイスとなっています。



Install
=======
::

  $ pip install django-elasticindex


サンプルコード
=======

リポジトリ内の、tests ディレクトリに動作するコードがあります。

1. Djangoのモデルの定義
----------------

models.py
::

    from django.db import models

    class DummyModel(models.Model):
        key = models.CharField(max_length=20, primary_key=True)
        value = models.TextField()


2. ElasticDocument クラスの定義
-------------------------

::

    from elasticindex.models import ElasticDocument, ElasticDocumentField as F

    class DummyESDocument(ElasticDocument):
        INDEX = "elasticindex_test"
        DOC_TYPE = "elasticindex_test_doc"
        ALLOW_KUROMOJI = False

        source_model = DummyModel

        key = F(mapping={"type": "string", "index": "not_analized"})
        value = F(mapping={"type": "string"})


3. データ流し込みバッチ
-------------

::

  DummyESDocument.rebuild_index()

rebuild_index() を実行すると、Elasticsearch 上にインデックスを作成し(存在しない場合)、
対応するDjango モデル ( DummyModel ) の全データを DB から読み出し、Elasticsearch に入れます。


3-1. 特定のモデルインスタンスのデータを入れる

::

  i = DummyModel.objects.get(key="xxx")
  DummyESDocument.rebuild_index_by_source_model(i)

これで、1レコードの更新ができます


4. 検索
-----

4-1. シンプルな検索

::

  results = DummyESDocument.objects.query({"match": {"key": "jumps"}})

results は、ElasticQuerySet のインスタンスです。

::

  result = list(results)[0]

検索を行い、result には DummyESDocument のインスタンスが入ります。


4-2. OR検索

::

    qs = DummyESDocument.objects.query(
        {"bool": {
            "should": [
                {"match": {"value": "dogs"}},
                {"match": {"value": "fox"}},

            ]}})

query は Elasticsearch の query をそのまま使います。


4-3. ソート順変更

::

    qs = DummyESDocument.objects.query({...})
    qs = qs.order_by({"key": "desc"})

Django のクエリセットのように、order_by をメソッドチェーンしてください。


4-4. 結果のスライシング

::

    qs = DummyESDocument.objects.query({...})
    results = qs[:100]

こちらも、Djangoのクエリセットのように、Python のスライシングを行うと範囲指定できます。
実行したタイミングでクエリが評価され、HTTPリクエストが発行されます。

また、.limit(), .offset() というメソッドもあり、メソッドチェーンで使えます。

::

    qs = DummyESDocument.objects.query({...})
    qs = qs.limit(20).offset(40).order_by({"created_at": "desc"})


4-5. パジネーション

Django のクエリセットのように、

::

    from django.core.paginator import Paginator

    qs = DummyESDocument.objects.query({...})
    paginator = Paginator(qs, 100)

    page = paginator.page(1)

    page.object_list...

Django の Paginator を用いてのパジネーションができます。


5. 設定
-----

5-1. ローカルエリアの ES を指定する場合

settings.py

::

  ELASTICINDEX_HOSTS = [{'host': '127.0.0.1', 'port': 9200}]

ELASTICINDEX_HOSTS を指定してください。


5-2. Amazon Elasticsearch Service を使う場合

::

    ELASTICINDEX_HOSTS = [
        {'host': 'xxxxxx.ap-northeast-1.es.amazonaws.com',
         'port': 443}]
    ELASTICINDEX_AWS_IAM = {
        'access_id': 'AWSACCESSID',
        'secret_key': 'AwsSecretKey******',
        'region': 'ap-northeast-1',
    }

Amazon ES へのアクセスを許可した IAM のクレデンシャルを settings に書いてください。

Amazon ES へのアクセス許可方法(IAMの作成方法)は Qiita に書きました

Amazon Elasticsearch Service を Python クライアントで、IAM アカウントを作ってセキュアにアクセスする - Qiita

http://qiita.com/ytyng/items/7c90c0b141aad9a12b38


6. テスト
------

クローンしたリポジトリで

::

  $ pip install -r requirements.txt
  $ ./runtest.py

実際に ES にアクセスを行う。
ESがローカルの 9200 ポートで動作していない場合は、local_settings.py を作成

local_settings.py
::

  ELASTICINDEX_HOSTS = [{'host': 'my-elasticsearch-host', 'port': 9200}]
