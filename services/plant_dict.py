"""
本地植物词库 — 用于名称联想，无需 API。
每条记录：(中文名, 英文名, 拉丁学名)
"""

PLANTS: list[tuple[str, str, str]] = [
    # 多肉 / 仙人掌
    ("虹之玉", "Jelly Bean Plant", "Sedum rubrotinctum"),
    ("玉露", "Haworthia", "Haworthia cooperi"),
    ("十二卷", "Zebra Plant", "Haworthiopsis attenuata"),
    ("熊童子", "Bear's Paw", "Cotyledon tomentosa"),
    ("黑法师", "Black Rose Aeonium", "Aeonium arboreum 'Atropurpureum'"),
    ("石莲花", "Echeveria", "Echeveria elegans"),
    ("仙人掌", "Cactus", "Cactaceae"),
    ("仙人球", "Ball Cactus", "Parodia magnifica"),
    ("芦荟", "Aloe Vera", "Aloe vera"),
    ("龙舌兰", "Agave", "Agave americana"),
    ("翡翠木", "Jade Plant", "Crassula ovata"),
    ("生石花", "Living Stone", "Lithops"),
    ("千佛手", "Sedum", "Sedum corynephyllum"),
    ("姬胧月", "Ghost Plant", "Graptopetalum paraguayense"),
    ("白牡丹", "White Peony Echeveria", "Graptoveria 'Titubans'"),
    ("桃蛋", "Peach Egg", "Graptopetalum amethystinum"),
    ("子持莲华", "Orostachys", "Orostachys iwarenge"),
    ("瓦松", "Rooftop Stonecrop", "Orostachys fimbriata"),
    ("不死鸟", "Mother of Thousands", "Kalanchoe daigremontiana"),
    ("月兔耳", "Chocolate Bunny", "Kalanchoe tomentosa"),
    ("福娘", "Cotyledon orbiculata", "Cotyledon orbiculata"),
    ("银手指", "Silver Torch Cactus", "Cleistocactus strausii"),
    # 观叶
    ("绿萝", "Pothos", "Epipremnum aureum"),
    ("龟背竹", "Monstera", "Monstera deliciosa"),
    ("虎皮兰", "Snake Plant", "Sansevieria trifasciata"),
    ("吊兰", "Spider Plant", "Chlorophytum comosum"),
    ("橡皮树", "Rubber Plant", "Ficus elastica"),
    ("琴叶榕", "Fiddle Leaf Fig", "Ficus lyrata"),
    ("发财树", "Money Tree", "Pachira aquatica"),
    ("幸运竹", "Lucky Bamboo", "Dracaena sanderiana"),
    ("铁线蕨", "Maidenhair Fern", "Adiantum capillus-veneris"),
    ("鸟巢蕨", "Bird's Nest Fern", "Asplenium nidus"),
    ("文竹", "Asparagus Fern", "Asparagus setaceus"),
    ("常春藤", "Ivy", "Hedera helix"),
    ("合果芋", "Arrowhead Plant", "Syngonium podophyllum"),
    ("花叶万年青", "Dieffenbachia", "Dieffenbachia seguine"),
    ("粗肋草", "Chinese Evergreen", "Aglaonema commutatum"),
    ("孔雀竹芋", "Peacock Plant", "Calathea makoyana"),
    ("斑马竹芋", "Zebra Plant", "Calathea zebrina"),
    ("鹿角蕨", "Staghorn Fern", "Platycerium bifurcatum"),
    ("波斯顿蕨", "Boston Fern", "Nephrolepis exaltata"),
    ("白鹤芋", "Peace Lily", "Spathiphyllum wallisii"),
    ("海芋", "Elephant Ear", "Alocasia macrorrhiza"),
    ("滴水观音", "Alocasia", "Alocasia odora"),
    ("棕竹", "Lady Palm", "Rhapis excelsa"),
    ("散尾葵", "Areca Palm", "Dypsis lutescens"),
    ("袖珍椰子", "Parlor Palm", "Chamaedorea elegans"),
    ("朱蕉", "Ti Plant", "Cordyline fruticosa"),
    ("彩虹竹芋", "Rainbow Calathea", "Calathea roseopicta"),
    ("网纹草", "Fittonia", "Fittonia albivenis"),
    ("椒草", "Peperomia", "Peperomia obtusifolia"),
    ("皱叶椒草", "Ripple Peperomia", "Peperomia caperata"),
    ("西瓜皮椒草", "Watermelon Peperomia", "Peperomia argyreia"),
    # 开花
    ("蝴蝶兰", "Phalaenopsis", "Phalaenopsis amabilis"),
    ("君子兰", "Kaffir Lily", "Clivia miniata"),
    ("茉莉", "Jasmine", "Jasminum sambac"),
    ("栀子花", "Gardenia", "Gardenia jasminoides"),
    ("月季", "Rose", "Rosa chinensis"),
    ("玫瑰", "Rose", "Rosa"),
    ("绣球花", "Hydrangea", "Hydrangea macrophylla"),
    ("长寿花", "Kalanchoe", "Kalanchoe blossfeldiana"),
    ("非洲紫罗兰", "African Violet", "Saintpaulia ionantha"),
    ("大岩桐", "Gloxinia", "Sinningia speciosa"),
    ("仙客来", "Cyclamen", "Cyclamen persicum"),
    ("报春花", "Primrose", "Primula vulgaris"),
    ("天竺葵", "Geranium", "Pelargonium hortorum"),
    ("凤仙花", "Impatiens", "Impatiens balsamina"),
    ("万寿菊", "Marigold", "Tagetes erecta"),
    ("三色堇", "Pansy", "Viola tricolor"),
    ("矮牵牛", "Petunia", "Petunia hybrida"),
    ("文心兰", "Dancing Lady Orchid", "Oncidium"),
    ("石斛兰", "Dendrobium", "Dendrobium nobile"),
    ("卡特兰", "Cattleya Orchid", "Cattleya"),
    ("朱顶红", "Amaryllis", "Hippeastrum"),
    ("水仙", "Daffodil", "Narcissus tazetta"),
    ("郁金香", "Tulip", "Tulipa gesneriana"),
    ("百合", "Lily", "Lilium"),
    ("薰衣草", "Lavender", "Lavandula angustifolia"),
    ("迷迭香", "Rosemary", "Salvia rosmarinus"),
    ("薄荷", "Mint", "Mentha"),
    ("罗勒", "Basil", "Ocimum basilicum"),
    # 木本 / 其他
    ("榕树", "Ficus", "Ficus microcarpa"),
    ("垂叶榕", "Weeping Fig", "Ficus benjamina"),
    ("金钱树", "ZZ Plant", "Zamioculcas zamiifolia"),
    ("鸭脚木", "Umbrella Tree", "Schefflera actinophylla"),
    ("含羞草", "Sensitive Plant", "Mimosa pudica"),
    ("捕蝇草", "Venus Flytrap", "Dionaea muscipula"),
    ("猪笼草", "Pitcher Plant", "Nepenthes"),
    ("瓶子草", "Trumpet Pitcher", "Sarracenia"),
    ("空气凤梨", "Air Plant", "Tillandsia"),
    ("水培风信子", "Hyacinth", "Hyacinthus orientalis"),
]


def search(query: str, limit: int = 6) -> list[dict]:
    """模糊匹配中文名、英文名、拉丁学名，返回最多 limit 条。"""
    q = query.strip().lower()
    if not q:
        return []

    results = []
    for zh, en, latin in PLANTS:
        if (
            q in zh.lower()
            or q in en.lower()
            or q in latin.lower()
        ):
            results.append({"zh": zh, "en": en, "latin": latin})
        if len(results) >= limit:
            break
    return results
