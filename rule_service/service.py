from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from .models import Rule, RuleStatus, RuleType
from .schemas import RuleCreate, RuleUpdate, RuleResponse
from database.database import get_db
import uuid

app = FastAPI()

@app.post("/rules", response_model=RuleResponse)
def create_rule(rule: RuleCreate, db: Session = Depends(get_db)):
    """创建新规则"""
    db_rule = Rule(
        id=str(uuid.uuid4()),
        fund_type=rule.fund_type,
        name=rule.name,
        description=rule.description,
        rule_type=rule.rule_type,
        content=rule.content,
        status=RuleStatus.DRAFT,
        priority=rule.priority
    )
    
    db.add(db_rule)
    db.commit()
    db.refresh(db_rule)
    return db_rule

@app.get("/rules/{rule_id}", response_model=RuleResponse)
def get_rule(rule_id: str, db: Session = Depends(get_db)):
    """获取规则详情"""
    rule = db.query(Rule).filter(Rule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule

@app.put("/rules/{rule_id}", response_model=RuleResponse)
def update_rule(rule_id: str, rule: RuleUpdate, db: Session = Depends(get_db)):
    """更新规则信息"""
    db_rule = db.query(Rule).filter(Rule.id == rule_id).first()
    if not db_rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    # 更新规则字段
    for key, value in rule.dict(exclude_unset=True).items():
        setattr(db_rule, key, value)
    
    db.commit()
    db.refresh(db_rule)
    return db_rule

@app.put("/rules/{rule_id}/status")
def update_rule_status(rule_id: str, status: RuleStatus, db: Session = Depends(get_db)):
    """更新规则状态"""
    rule = db.query(Rule).filter(Rule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    rule.status = status
    db.commit()
    return {"message": "Rule status updated successfully"}

@app.get("/rules/fund/{fund_type}")
def get_rules_by_fund_type(fund_type: str, status: RuleStatus = RuleStatus.ACTIVE, db: Session = Depends(get_db)):
    """根据基金类型获取规则"""
    rules = db.query(Rule).filter(
        Rule.fund_type == fund_type,
        Rule.status == status
    ).order_by(Rule.priority.desc()).all()
    return rules