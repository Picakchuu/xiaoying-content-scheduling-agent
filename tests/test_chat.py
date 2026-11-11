import json
import unittest
from content_agent.chat import chat
from content_agent.intake import Intake, prepare_request, read_attachment
from content_agent.models import MockModel
from content_agent.storage import Store, ConflictError
from content_agent.domain import validate_request
from content_agent.tools import DEFAULT_CATALOG
from support import temporary_workspace
from test_tools_storage import NOW


class ChatTests(unittest.TestCase):
    def setUp(self):
        self.root = temporary_workspace(self)
        self.store = Store(self.root/'state.db')

    def conversation(self, lines, model=None):
        lines=iter(lines)
        emitted=[]
        chat(model or MockModel(),self.store,catalog=DEFAULT_CATALOG,clock=lambda:NOW,
             read=lambda prompt:next(lines),emit=emitted.append)
        return '\n'.join(emitted)

    def test_missing_constraints_do_not_execute_then_follow_up(self):
        text=self.conversation(['做新品活动','/run','预算10模拟单位，2026-11-12 18:00前完成','/run','/repeat','/exit'])
        self.assertIn('尚不能执行',text)
        self.assertIn('必填项已齐',text)
        self.assertIn('状态：completed',text)
        self.assertIn('重复重放：True',text)

    def test_file_validation_and_digest_identity(self):
        file=self.root/'materials.json'
        file.write_text(json.dumps({'materials':[{'id':'custom','title':'新品素材','summary':'新品活动信息','tags':['新品']}]}),encoding='utf-8')
        attachment=read_attachment(file)
        draft={'theme':'新品','budget':10,'deadline':'2026-11-12T18:00:00+08:00'}
        original=validate_request(prepare_request('x',draft,[attachment]),now=NOW).request
        self.store.start(original)
        attachment['digest']='0'*64
        changed=validate_request(prepare_request('x',draft,[attachment]),now=NOW).request
        with self.assertRaises(ConflictError):
            self.store.start(changed)

    def test_custom_materials_used(self):
        file=self.root/'materials.json'
        file.write_text(json.dumps({'materials':[{'id':'custom','title':'新品素材','summary':'本地新品活动资料','tags':['新品']}]}),encoding='utf-8')
        text=self.conversation(['/attach '+str(file),'新品活动，预算10模拟单位，2026-11-12 18:00前完成','/run','/exit'])
        self.assertIn('状态：completed',text)
        self.assertIn('本地新品活动资料',text)

    def test_unsupported_and_large_files(self):
        bad=self.root/'file.pdf'
        bad.write_bytes(b'test')
        with self.assertRaises(ValueError):
            read_attachment(bad)
        big=self.root/'big.txt'
        big.write_bytes(b'x'*(128*1024+1))
        with self.assertRaises(ValueError):
            read_attachment(big)

    def test_real_extractor_retains_draft_and_rejects_fake_budget(self):
        class Model:
            def complete(self,system,ctx):
                self.context=ctx
                return json.dumps({'theme':'新品','budget':True,'deadline':None,'uncertainties':[]})
        model=Model()
        with self.assertRaises(ValueError):
            Intake(model).extract(['预算10'],{'theme':'新品'},[],NOW)
        self.assertEqual(model.context['draft'],{'theme':'新品'})

    def test_ambiguous_deadline_never_defaults(self):
        draft=Intake().extract(['新品活动，预算10模拟单位，尽快完成'],{},[],NOW)
        self.assertIsNone(draft['deadline'])

    def test_eof_exits(self):
        def eof(prompt):
            raise EOFError()
        self.assertEqual(chat(MockModel(),self.store,catalog=DEFAULT_CATALOG,read=eof,emit=lambda _:None),0)

    def test_failed_correction_does_not_execute_old_draft(self):
        class Model:
            mode='real'
            name='intake-fixture'
            count=0
            def complete(self,system,ctx):
                self.count+=1
                if self.count==2:
                    raise ValueError('bad output')
                return json.dumps({'theme':'新品','budget':10,'deadline':'2026-11-12T18:00:00+08:00','uncertainties':[]})
        text=self.conversation(['新品活动预算10','改成另一个预算','/run','/exit'],Model())
        self.assertIn('需求解析失败',text)
        self.assertIn('尚不能执行',text)
        with self.store.connect() as conn:
            self.assertEqual(conn.execute('SELECT count(*) FROM runs').fetchone()[0],0)
