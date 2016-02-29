class ElasticDocumentField(object):
    """
    ElasticDocumentようのField
    score = ElasticDocumentField(default=0) みたいに使う。

    :param default: 値を取得時、無かった場合と None だった場合のデフォルト値
    :param verbose_name: Django モデルフィールドの verbose_name の代用。
        指定はできるが内部では使っていないので、指定しても意味ない
    """

    class AttrNotFoundInSourceModel(Exception):
        pass

    def __init__(self, verbose_name=None, mapping=None,
                 source_attr_name=None, source_value_getter=None):
        self.verbose_name = verbose_name
        self.mapping = mapping or {}
        self.source_attr_name = source_attr_name
        self.source_value_getter = source_value_getter

    def contribute_to_class(self, cls, name):
        self.model = cls
        self.name = name

    def get_value_for_index_of_source_model(self, source_model):
        """
        Djangoモデルからインデックス用の値を取得
        """
        if self.source_value_getter:
            return self.source_value_getter(source_model)
        attr_name = self.source_attr_name or self.name
        if not hasattr(source_model, attr_name):
            raise self.AttrNotFoundInSourceModel(attr_name)
        return getattr(source_model, attr_name)

    def get_value_from_index_source_value(self, index_source_value):
        """
        Elasticsearch の、検索結果の _source の値からPython に使える値に変換
        ES から返ってくる値は、int や リストなどの方を保持したまま取得できるので
        通常は変換不要
        """
        return index_source_value
