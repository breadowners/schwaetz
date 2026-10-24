# Third-party components

The application source is Apache-2.0. This does not relicense external packages,
models or datasets. No model weights, third-party runtime source, dictionary,
class handouts or recordings are bundled in this repository.

| Component | Source and terms |
| --- | --- |
| Adapted ZIPA/icefall inference | [ZIPA](https://github.com/lingjzhu/zipa/tree/21e9e8aa4cc6c130cb05d836a1979886f9245302): repository MIT notice retained in `licenses/ZIPA-MIT.txt`; the Zipformer/scaling files have Xiaomi Apache-2.0 headers. Modified inference adapters are identified in `NOTICE`. |
| Recognition checkpoint | [ZLS large-v3-turbo](https://huggingface.co/ZLSCompLing/Whisper-Large-V3-Turbo-Luxembourgish): model card labels MIT. Downloaded separately. |
| Phonetic checkpoint | [Luxembourgish ZIPA fine-tune](https://huggingface.co/pgilles/zipa-large-crctc-luxembourgish-ipapack20): card labels MIT, while its linked upstream `ns` base weights are CC BY-NC-SA 4.0. Do not assume unrestricted commercial or redistribution rights from the fine-tune label. Models are downloaded separately; clarify the upstream terms for your intended use. |
| Pronunciation dictionary | [Luxembourgish MFA dictionary](https://github.com/PeterGilles/Luxembourgish_in_Montreal_Forced_Aligner): Apache-2.0, downloaded with its license. |
| Piper engine | [Piper](https://github.com/OHF-Voice/piper1-gpl): GPL-3.0. Installed as a separate Python dependency; its source and license obligations remain applicable. |
| Luxembourgish Piper voice | [Marco Barnig voice](https://huggingface.co/mbarnig/lb_rhasspy_piper_tts), trained with ZLS data: model card labels CC BY 4.0; [linked data entry](https://data.public.lu/en/datasets/lb-rhasspy-piper-female-tts-2/) labels CC BY-SA 4.0. Preserve attribution and resolve this discrepancy before redistribution. |
| Apple GPU encoder | [MLX Whisper](https://github.com/ml-explore/mlx-examples/tree/main/whisper), MIT; [CTranslate2](https://github.com/OpenNMT/CTranslate2), MIT. Imported dependencies; no weights bundled. |

The download script retrieves upstream runtime license files and keeps downloaded
artifacts in ignored `models/`. Other packages retain the licenses supplied with
their distributions. The free OpenCode promotion is an external hosted service,
not an open-source model distribution or a permanent availability guarantee.

## Listening sources

The listening catalog links to INLL's Poterkëscht publisher pages, podcast RSS
enclosures, and official textbook companion pages. INLL and the respective
publishers retain their rights in those recordings, books and transcripts. The
repository contains source URLs, metadata, original practice guides and generated
practice questions; no original podcast files, books or full publisher transcripts
are bundled or relicensed under Apache-2.0. Downloads stay in ignored `.cache/`.
Public accessibility of a recording does not itself grant redistribution rights;
check the publisher's terms before mirroring recordings for a hosted audience.

Privately configured translated class notes are read only on personal deployments.
Public mode ignores those notes. Practice questions and AI translations are study
support, not official INLL assessments or translations. The project is independent
and is not presented as endorsed by INLL, ZLS, the University of Luxembourg or the
listed model providers.
